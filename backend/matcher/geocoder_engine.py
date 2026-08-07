import re
from typing import Dict, Any, List
from .pincode_db import pincode_db
from .osm_client import search_landmarks_near_coordinates

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


def extract_search_terms(locality: str, landmark: str) -> List[str]:
    """
    Extracts ordered list of search terms from locality/landmark fields.
    Returns most-specific term first, broader locality fallback second.
    """
    terms = []

    # --- Primary: explicit landmark field ---
    if landmark:
        cleaned = _clean(landmark)
        if cleaned:
            terms.append(cleaned)

    # --- Secondary: parse locality for landmark-style fragment ---
    if locality:
        # Split on comma to separate landmark hint from area name
        parts = [p.strip() for p in locality.split(',')]
        for part in parts:
            cleaned = _clean(part)
            if not cleaned:
                continue
            words = [w for w in cleaned.split() if len(w) > 2]
            if not words:
                continue
            # Build a search phrase from first 3 meaningful words
            phrase = ' '.join(words[:3])
            if phrase not in terms:
                terms.append(phrase)

    return terms


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

    if not pincode:
        return {
            "status": "error",
            "message": "No pincode provided in the parsed JSON.",
            "possible_addresses": []
        }

    # Ground truth: resolve pincode to base lat/lon
    coords = pincode_db.get_coordinates(pincode)
    if not coords:
        return {
            "status": "error",
            "message": f"Could not find coordinates for pincode {pincode}.",
            "possible_addresses": []
        }

    lat, lon = coords

    # Build ordered search terms (specific -> broad)
    search_terms = extract_search_terms(locality, landmark)

    # Add city as the broadest fallback context
    if city:
        search_terms.append(_clean(city))

    possible_addresses = []
    used_term = None

    for term in search_terms:
        if not term:
            continue
        results = await search_landmarks_near_coordinates(term, lat, lon, radius=500)
        if results:
            possible_addresses = results
            used_term = term
            break

    return {
        "status": "success",
        "base_coordinates": {"latitude": lat, "longitude": lon},
        "search_radius_meters": 1000,
        "search_terms_tried": search_terms,
        "matched_on_term": used_term,
        "possible_addresses": possible_addresses,
        "input_address": parsed_json
    }
