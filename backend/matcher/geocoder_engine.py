import re
from typing import Dict, Any, List
from .pincode_db import pincode_db
from .osm_client import search_landmarks_near_coordinates, search_structured_address, get_pincode_boundary

# Common positional/directional words to strip before landmark extraction
_DIRECTIONAL = re.compile(
    r'\b(opp(?:osite)?|near|beside|behind|next\s+to|adj(?:acent\s+to)?)\b\s*',
    re.IGNORECASE
)
# City/state noise words to remove
_CITY_NOISE = re.compile(
    r'\b(hyd|hyderabad|secunderabad|city|town|andhra\s+pradesh|telangana)\b',
    re.IGNORECASE
)


def _clean(text: str) -> str:
    """Strip directional prefixes and city noise from a text fragment."""
    text = _DIRECTIONAL.sub('', text)
    text = _CITY_NOISE.sub('', text)
    return text.strip(' ,;-')


def extract_search_terms(house_no: str, locality: str, landmark: str, city: str = "") -> List[str]:
    """
    Extracts ordered list of search terms from address fields.
    Returns most-specific term first (including house_no if present).
    Does not truncate locality arbitrarily.
    """
    terms = []
    
    clean_landmark = _clean(landmark) if landmark else ""
    clean_locality_str = _clean(locality) if locality else ""

    clean_city = _clean(city) if city else ""

    # Permutations (from most precise to least precise)
    # 1. House + Landmark + Locality + City
    if house_no and clean_landmark and clean_locality_str and clean_city:
        terms.append(f"{house_no} {clean_landmark} {clean_locality_str} {clean_city}".strip())
        
    # 2. Landmark + Locality + City
    if clean_landmark and clean_locality_str and clean_city:
        terms.append(f"{clean_landmark} {clean_locality_str} {clean_city}".strip())

    # 3. House + Landmark + Locality
    if house_no and clean_landmark and clean_locality_str:
        terms.append(f"{house_no} {clean_landmark} {clean_locality_str}".strip())
    
    # 4. House + Locality
    if house_no and clean_locality_str:
        terms.append(f"{house_no} {clean_locality_str}".strip())
        
    # 5. House + Landmark
    if house_no and clean_landmark:
        terms.append(f"{house_no} {clean_landmark}".strip())

    # 6. Landmark + Locality
    if clean_landmark and clean_locality_str:
        terms.append(f"{clean_landmark} {clean_locality_str}".strip())
        
    # 7. Locality + City
    if clean_locality_str and clean_city:
        terms.append(f"{clean_locality_str} {clean_city}".strip())

    # 8. Landmark exactly
    if clean_landmark:
        terms.append(clean_landmark)

    # 9. Locality exactly
    if clean_locality_str:
        terms.append(clean_locality_str)
        
    # 10. Locality parts (e.g. if locality is "5th line, Devinagar", try "Devinagar, City")
    if locality:
        parts = [p.strip() for p in locality.split(',')]
        for part in reversed(parts):  # usually broader areas are at the end, which map better
            cleaned_part = _clean(part)
            if cleaned_part:
                if clean_city:
                    terms.append(f"{cleaned_part} {clean_city}".strip())
                terms.append(cleaned_part)
                
    # Remove duplicates while preserving order
    unique_terms = []
    for term in terms:
        if term and term not in unique_terms:
            unique_terms.append(term)

    return unique_terms


async def geocode_address(parsed_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes Step 2: Ground Truth and Landmark Geocoding.
    Resolves base coordinates via Pincode DB and searches for precise POIs via Nominatim.
    Outputs the payload to be passed to Step 3.
    """
    pincode = parsed_json.get("pincode")
    locality = parsed_json.get("locality")
    landmark = parsed_json.get("landmark")
    city = parsed_json.get("city")
    house_no = parsed_json.get("house_no")

    if not pincode:
        return {
            "status": "error",
            "message": "No pincode provided in the parsed JSON.",
            "possible_addresses": []
        }

    # Get the bounding box from OSM for the pincode.
    boundary_info = await get_pincode_boundary(pincode)
    
    viewbox_str = None
    if boundary_info:
        viewbox_str, lat, lon = boundary_info
        print(f"Using dynamic OSM boundary for pincode {pincode}: {viewbox_str}")
        radius = 1500 # fallback radius context
    else:
        # Resolve via local db
        coords = pincode_db.get_coordinates(pincode)
        if not coords:
            return {
                "status": "unresolved",
                "reason": f"Pincode {pincode} not found in database and OSM."
            }
        lat, lon = coords
        print(f"Fallback to CSV database for pincode {pincode}: {lat}, {lon}")
        radius = 5000 # Use a generous 5km radius for the inaccurate CSV database

    # 1. Attempt structured search first for maximum pinpoint accuracy
    if house_no and locality:
        # Combine house_no and locality for the 'street' parameter in OSM
        street_query = f"{house_no} {_clean(locality)}"
        structured_results = await search_structured_address(
            street=street_query,
            city=_clean(city) if city else "",
            postalcode=pincode,
            lat=lat,
            lon=lon,
            radius=1500
        )
        if structured_results:
            return {
                "status": "success",
                "base_coordinates": {"latitude": lat, "longitude": lon},
                "search_radius_meters": 1000,
                "search_terms_tried": [f"structured: {street_query}"],
                "matched_on_term": f"structured: {street_query}",
                "possible_addresses": structured_results,
                "input_address": parsed_json
            }

    # Build ordered search terms (specific -> broad) for fallback
    search_terms = extract_search_terms(house_no, locality, landmark, city)

    possible_addresses = []
    used_term = None

    for term in search_terms:
        if not term:
            continue
        results = await search_landmarks_near_coordinates(term, lat, lon, radius=radius, viewbox_str=viewbox_str)
        if results:
            possible_addresses = results
            used_term = term
            break

    return {
        "status": "success",
        "base_coordinates": {"latitude": lat, "longitude": lon},
        "search_radius_meters": radius,
        "search_terms_tried": search_terms,
        "matched_on_term": used_term,
        "possible_addresses": possible_addresses,
        "input_address": parsed_json
    }
