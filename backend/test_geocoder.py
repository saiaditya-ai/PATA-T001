import asyncio
import json
import sys
import os
import httpx
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matcher.pincode_db import pincode_db
from matcher.osm_client import search_landmarks_near_coordinates, detect_landmark_type
from matcher.geocoder_engine import geocode_address, extract_search_terms

# Real address: 60-4-9, Sandireddi Narayana Rd, Mogalrajapuram, Vijayawada 520010
payload = {
  "house_no": "30 118",
  "locality": "near tagore bomma centre arundelpet",
  "city": "guntur",
  "pincode": "522002",
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
                params={"q": "Mogalrajapuram Vijayawada", "format": "json", "limit": 1},
                headers={"User-Agent": "PataAI/1.0"}
            )
        elapsed = time.time() - t0
        print(f"Status: {r.status_code}  |  Time: {elapsed:.2f}s")
        data = r.json()
        if data:
            print(f"[OK] Nominatim reachable -- sample: {data[0].get('display_name', '')[:80]}")
        else:
            print("[OK] Nominatim reachable but returned 0 results")
    except Exception as e:
        print(f"[FAIL] {e}")

async def test_osm_client():
    print("\n" + "=" * 55)
    print("PHASE 2: search_landmarks_near_coordinates()")
    print("=" * 55)

    # Derive everything from the payload - no hardcoded values
    coords = pincode_db.get_coordinates(payload["pincode"])
    if not coords:
        print(f"[FAIL] Could not resolve pincode {payload['pincode']}")
        return
    lat, lon = coords
    terms = extract_search_terms(payload.get("locality"), payload.get("landmark"))
    if payload.get("city"):
        terms.append(payload["city"])

    print(f"  Pincode {payload['pincode']} -> lat={lat:.4f}, lon={lon:.4f}")
    print(f"  Search terms (cascade): {terms}")
    for t in terms:
        ltype = detect_landmark_type(t)
        print(f"    '{t}' -> type hint: {ltype if ltype else 'none (free text)'}")
    print(f"  Radius: 1000m")

    t0 = time.time()
    for term in terms:
        results = await search_landmarks_near_coordinates(term, lat, lon, radius=1000)
        elapsed = time.time() - t0
        print(f"  Term '{term}': {len(results)} results  ({elapsed:.2f}s)")
        if results:
            print(json.dumps(results[:3], indent=2))
            break
    else:
        print("  No results from any term.")

async def test_geocoder():
    print("\n" + "=" * 55)
    print("PHASE 3: Full geocode_address() pipeline")
    print("=" * 55)
    t0 = time.time()
    result = await geocode_address(payload)
    elapsed = time.time() - t0
    print(f"Time: {elapsed:.2f}s")
    print(json.dumps(result, indent=2))

async def main():
    await test_nominatim_connectivity()
    await test_osm_client()
    await test_geocoder()

if __name__ == "__main__":
    asyncio.run(main())
