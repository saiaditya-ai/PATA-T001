import re
import math
from typing import Dict, Any, List
from .pincode_db import pincode_db

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
    Executes Step 2: Ground Truth and Geocoding.
    Since OSM results are unreliable for hyper-local Indian addresses, we rely purely 
    on the parser's extraction and resolve to the pincode base coordinates.
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

    # Build ordered search terms (for downstream reference if needed)
    search_terms = extract_search_terms(locality, landmark)
    if city:
        search_terms.append(_clean(city))

    # Rely purely on Gemini parsing + Pincode base lat/lon, skipping OSM
    # The output format is preserved for compatibility with downstream processes.
    pincode_candidate = {
        "name": f"{pincode} General Area",
        "type": "pincode",
        "osm_type": "node",
        "coordinates": {"latitude": lat, "longitude": lon},
        "address": {"postcode": pincode, "city": city or ""}
    }

    return {
        "status": "success",
        "base_coordinates": {"latitude": lat, "longitude": lon},
        "search_radius_meters": 1000,
        "search_terms_tried": search_terms,
        "matched_on_term": "pincode_fallback",
        "possible_addresses": [pincode_candidate],
        "input_address": parsed_json
    }
