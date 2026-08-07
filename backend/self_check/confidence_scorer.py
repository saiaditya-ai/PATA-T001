import math
from typing import Dict, Any, List, Optional, Tuple

def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in meters between two lat/lon points."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _score_candidate(
    candidate: Dict[str, Any],
    base_lat: float,
    base_lon: float,
    search_terms: List[str],
    input_address: Dict[str, Any],
    radius: int = 1000,
) -> Dict[str, Any]:
    """
    Scores a single candidate POI against the input address.
    Returns the candidate dict enriched with score details.
    """
    coords = candidate.get("coordinates", {})
    cand_lat = coords.get("latitude", 0.0)
    cand_lon = coords.get("longitude", 0.0)

    # --- 1. Distance score (0.0 – 0.4) ---
    # Full score if within radius, degrades linearly to 0 at 3x radius
    dist_m = _haversine_meters(base_lat, base_lon, cand_lat, cand_lon)
    max_dist = radius * 3
    dist_score = max(0.0, (1.0 - dist_m / max_dist)) * 0.40

    # --- 2. Name relevance score (0.0 – 0.35) ---
    name = candidate.get("name", "").lower()
    name_score = 0.0
    matched_term = None
    for term in search_terms:
        words = [w for w in term.lower().split() if len(w) > 2]
        hits = sum(1 for w in words if w in name)
        if words:
            ratio = hits / len(words)
            if ratio > name_score:
                name_score = ratio
                matched_term = term
    name_score *= 0.35

    # --- 3. Pincode match score (0.0 – 0.15) ---
    candidate_postcode = candidate.get("address", {}).get("postcode", "")
    input_pincode = str(input_address.get("pincode", "")).strip()
    pincode_score = 0.15 if (input_pincode and candidate_postcode == input_pincode) else 0.0

    # --- 4. City match score (0.0 – 0.10) ---
    candidate_city = candidate.get("address", {}).get("city", "").lower()
    input_city = (input_address.get("city") or "").lower()
    city_score = 0.10 if (input_city and input_city in candidate_city) else 0.0

    total = round(dist_score + name_score + pincode_score + city_score, 4)

    return {
        **candidate,
        "scoring": {
            "total_score": total,
            "distance_meters": round(dist_m, 1),
            "dist_score": round(dist_score, 4),
            "name_score": round(name_score, 4),
            "pincode_score": round(pincode_score, 4),
            "city_score": round(city_score, 4),
            "matched_term": matched_term,
        }
    }


def rank_candidates(geocoder_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes the Step 2 geocoder output and returns a ranked list of candidates
    with confidence scores. The top candidate is the best match.
    """
    candidates: List[Dict] = geocoder_output.get("possible_addresses", [])
    base = geocoder_output.get("base_coordinates", {})
    base_lat = base.get("latitude", 0.0)
    base_lon = base.get("longitude", 0.0)
    search_terms: List[str] = geocoder_output.get("search_terms_tried", [])
    input_address: Dict = geocoder_output.get("input_address", {})
    radius: int = geocoder_output.get("search_radius_meters", 1000)

    if not candidates:
        return {
            "status": "no_candidates",
            "base_coordinates": base,
            "ranked_candidates": [],
            "best_match": None,
            "confidence_score": 0.0,
            "confidence_level": "very_low",
            "input_address": input_address,
        }

    scored = [
        _score_candidate(c, base_lat, base_lon, search_terms, input_address, radius)
        for c in candidates
    ]
    scored.sort(key=lambda x: x["scoring"]["total_score"], reverse=True)

    best = scored[0]
    best_score = best["scoring"]["total_score"]

    # Confidence level buckets
    if best_score >= 0.75:
        level = "high"
    elif best_score >= 0.50:
        level = "medium"
    elif best_score >= 0.25:
        level = "low"
    else:
        level = "very_low"

    return {
        "status": "ranked",
        "base_coordinates": base,
        "ranked_candidates": scored,
        "best_match": best,
        "confidence_score": best_score,
        "confidence_level": level,
        "input_address": input_address,
    }
