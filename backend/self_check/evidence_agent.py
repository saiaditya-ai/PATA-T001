import os
import json
from typing import Dict, Any
from google import genai
from google.genai import types

_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment.")
        _client = genai.Client(api_key=api_key)
    return _client


async def generate_justification(scored_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes the confidence_scorer output and calls Gemini Flash to generate
    a concise, driver-facing justification for the best matched location.
    Returns the final Step 3 payload.
    """
    best = scored_output.get("best_match")
    input_address = scored_output.get("input_address", {})
    confidence_score = scored_output.get("confidence_score", 0.0)
    confidence_level = scored_output.get("confidence_level", "very_low")
    base_coords = scored_output.get("base_coordinates", {})

    # If no candidates at all, return a clean fallback
    if not best:
        return {
            "status": "unresolved",
            "confidence_score": 0.0,
            "confidence_level": "very_low",
            "resolved_location": None,
            "justification": "Could not resolve any landmarks for the given address. Using pincode base coordinates.",
            "input_address": input_address,
            "base_coordinates": base_coords,
        }

    scoring = best.get("scoring", {})
    best_coords = best.get("coordinates", {})
    best_name = best.get("name", "Unknown")
    best_type = best.get("type", "unknown")

    prompt = f"""You are an address resolution AI for last-mile delivery in India.

Given the following information, write a short (2-3 sentences), driver-facing justification explaining WHY this location is the best match for the delivery address. Be specific and confident. Do NOT use JSON — plain English only.

Input Address:
- House/Unit: {input_address.get('house_no')}
- Locality: {input_address.get('locality')}
- Landmark: {input_address.get('landmark')}
- City: {input_address.get('city')}
- Pincode: {input_address.get('pincode')}

Best Matched Location:
- Name: {best_name}
- Type: {best_type}
- Coordinates: {best_coords.get('latitude')}, {best_coords.get('longitude')}
- Distance from pincode centre: {scoring.get('distance_meters')}m
- Pincode match: {"Yes" if scoring.get('pincode_score', 0) > 0 else "No"}
- Name relevance score: {scoring.get('name_score')}
- Overall confidence: {confidence_level} ({confidence_score:.2f}/1.00)

Write the justification now:"""

    justification_text = ""
    try:
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=200,
                temperature=0.3,
            )
        )
        justification_text = response.text.strip()
    except Exception as e:
        justification_text = (
            f"Matched to '{best_name}' ({best_type}) at "
            f"{best_coords.get('latitude'):.4f}, {best_coords.get('longitude'):.4f}, "
            f"{scoring.get('distance_meters')}m from pincode centre. "
            f"Confidence: {confidence_level} ({confidence_score:.2f})."
        )

    return {
        "status": "resolved",
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "resolved_location": {
            "name": best_name,
            "type": best_type,
            "coordinates": best_coords,
            "distance_from_pincode_centre_m": scoring.get("distance_meters"),
            "matched_on_term": scoring.get("matched_term"),
        },
        "justification": justification_text,
        "all_candidates_ranked": [
            {
                "name": c.get("name", "")[:80],
                "type": c.get("type", ""),
                "score": c.get("scoring", {}).get("total_score", 0),
                "distance_m": c.get("scoring", {}).get("distance_meters", 0),
                "coordinates": c.get("coordinates", {}),
            }
            for c in scored_output.get("ranked_candidates", [])
        ],
        "input_address": input_address,
        "base_coordinates": base_coords,
    }
