import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import AddressRequest

from parsers import libpostal_parser, gemini_flash_parser, local_parser
from matcher.geocoder_engine import geocode_address
from self_check.confidence_scorer import rank_candidates
from self_check.evidence_agent import generate_justification

app = FastAPI(title="Pata AI - Address Intelligence Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/geocode")
async def geocode(request: AddressRequest):
    start_time = time.time()
    raw_address = request.raw_address

    if not raw_address:
        raw_address = request.dict().get("address", "")
        if not raw_address:
            raise HTTPException(status_code=400, detail="Address is required")

    try:
        best_confidence = -1
        best_scored_output = None
        best_parsed_json = None
        best_parser_used = None

        parsers_to_try = [
            (libpostal_parser.parse, "libpostal", False),
            (gemini_flash_parser.parse, "gemini_flash", True),
            (local_parser.parse, "local_model", True)
        ]

        for parse_func, parser_name, is_async in parsers_to_try:
            try:
                if is_async:
                    parsed_address = await parse_func(raw_address)  # type: ignore
                else:
                    parsed_address = parse_func(raw_address)
                
                parsed_json = parsed_address.dict()
                
                # Step 2: Geocode
                geocoder_output = await geocode_address(parsed_json)
                
                # Step 3: Score
                scored_output = rank_candidates(geocoder_output)
                confidence = scored_output.get("confidence_score", 0.0)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_scored_output = scored_output
                    best_parsed_json = parsed_json
                    best_parser_used = parser_name

                if confidence >= 0.50:
                    break
                else:
                    print(f"[{parser_name}] Confidence {confidence} < 0.50. Falling back...")

            except Exception as e:
                print(f"[{parser_name}] Error: {e}. Falling back...")
                continue
                
        if not best_scored_output:
            raise HTTPException(status_code=500, detail="All parsing tiers failed.")

        # Step 4: Evidence Justification
        final_output = await generate_justification(best_scored_output)
        
        resolved = final_output.get("resolved_location") or {}
        coords = resolved.get("coordinates") or final_output.get("base_coordinates") or {}

        latency_ms = (time.time() - start_time) * 1000

        # Construct response format expected by frontend
        response = {
            "parsed_address": {
                **best_parsed_json,
                "parser_used": best_parser_used
            },
            "geocoding": {
                "latitude": coords.get("latitude"),
                "longitude": coords.get("longitude"),
                "matched_pincode": best_parsed_json.get("pincode"),
                "matched_area": best_parsed_json.get("locality"),
                "matched_landmark": resolved.get("name")
            },
            "validation": {
                "confidence_score": final_output.get("confidence_score", 0.0),
                "is_high_confidence": final_output.get("confidence_level") == "high",
                "evidence_justification": final_output.get("justification", "")
            },
            "metrics": {
                "latency_ms": round(latency_ms, 2)
            }
        }

        return response
    
    except Exception as e:
        print(f"Error processing address: {e}")
        raise HTTPException(status_code=500, detail=str(e))
