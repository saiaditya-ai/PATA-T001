import asyncio
import json
import sys
import os
import httpx
import time
from dotenv import load_dotenv

# Load .env for GEMINI_API_KEY
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matcher.pincode_db import pincode_db
from matcher.osm_client import search_landmarks_near_coordinates, detect_landmark_type
from matcher.geocoder_engine import geocode_address, extract_search_terms
from self_check.confidence_scorer import rank_candidates
from self_check.evidence_agent import generate_justification

# Test address: near Tagore Bomma Centre, Arundelpet, Guntur
payload = {
  "house_no": "42-2/1-206/1a",
  "locality": "3rd right 5th line",
  "city": "devinagar vijayawada",
  "pincode": "520003",
  "landmark": None,
  "direction": None,
  "language_detected": "en"
}

async def test_nominatim_connectivity():
    print("=" * 55)
    print("PHASE 1: Nominatim connectivity check")
    print("=" * 55)
    try:
        t0 = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": "Arundelpet Guntur", "format": "json", "limit": 1},
                headers={"User-Agent": "PataAI/1.0"}
            )
        elapsed = time.time() - t0
        data = r.json()
        if data:
            print(f"[OK] {r.status_code} in {elapsed:.2f}s -- {data[0].get('display_name','')[:70]}")
        else:
            print(f"[OK] {r.status_code} in {elapsed:.2f}s -- 0 results")
    except Exception as e:
        print(f"[FAIL] {e}")

async def test_osm_client():
    print("\n" + "=" * 55)
    print("PHASE 2: search_landmarks_near_coordinates()")
    print("=" * 55)
    coords = pincode_db.get_coordinates(payload["pincode"])
    if not coords:
        print(f"[FAIL] Could not resolve pincode {payload['pincode']}")
        return
    lat, lon = coords
    terms = extract_search_terms(payload.get("locality"), payload.get("landmark"))
    if payload.get("city"):
        terms.append(payload["city"])

    print(f"  Pincode {payload['pincode']} -> lat={lat:.4f}, lon={lon:.4f}")
    for t in terms:
        ltype = detect_landmark_type(t)
        print(f"    '{t}' -> type: {ltype if ltype else 'free text'}")

    t0 = time.time()
    for term in terms:
        results = await search_landmarks_near_coordinates(term, lat, lon, radius=1000)
        elapsed = time.time() - t0
        print(f"  Term '{term}': {len(results)} results ({elapsed:.2f}s)")
        if results:
            print(json.dumps(results[:2], indent=2))
            break
    else:
        print("  No results from any term.")

async def test_full_pipeline():
    print("\n" + "=" * 55)
    print("PHASE 3: Full pipeline (Geocode -> Score -> Justify)")
    print("=" * 55)
    t0 = time.time()

    # Step 2
    geocoder_output = await geocode_address(payload)
    print(f"  Step 2 done: {len(geocoder_output.get('possible_addresses', []))} candidates, "
          f"matched on '{geocoder_output.get('matched_on_term')}'")

    # Step 3a: Score
    scored = rank_candidates(geocoder_output)
    print(f"  Step 3a done: best='{scored.get('best_match', {}).get('name', 'None')[:60]}' "
          f"score={scored.get('confidence_score')} level={scored.get('confidence_level')}")

    # Step 3b: LLM Justification
    final = await generate_justification(scored)

    elapsed = time.time() - t0
    print(f"\n  Total pipeline time: {elapsed:.2f}s\n")
    print(json.dumps(final, indent=2))

async def main():
    await test_nominatim_connectivity()
    await test_osm_client()
    await test_full_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
