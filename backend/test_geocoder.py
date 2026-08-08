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
from matcher.geocoder_engine import geocode_address
from self_check.confidence_scorer import rank_candidates
from self_check.evidence_agent import generate_justification

# Test address
payload = {
  "house_no": "Akshara",
  "locality": "5th line donka road",
  "city": "Guntur",
  "pincode": "522002",
  "landmark": "Shri hospital",
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
                params={"q": "India", "format": "json", "limit": 1},
                headers={"User-Agent": "PataAI/1.0"}
            )
        elapsed = time.time() - t0
        data = r.json()
        if data:
            print(f"[OK] {r.status_code} in {elapsed:.2f}s -- Successfully connected to Nominatim.")
        else:
            print(f"[OK] {r.status_code} in {elapsed:.2f}s -- 0 results")
    except Exception as e:
        print(f"[FAIL] {e}")


async def test_full_pipeline():
    print("\n" + "=" * 55)
    print("PHASE 3: Full pipeline (Geocode -> Score -> Justify)")
    print("=" * 55)
    t0 = time.time()

    # Step 2
    geocoder_output = await geocode_address(payload)
    print(f"  Step 2 done: base lat/lon resolved.")

    # Step 3a: Score
    scored = rank_candidates(geocoder_output)
    print(f"  Step 3a done: score={scored.get('confidence_score')} level={scored.get('confidence_level')}")

    # Step 3b: LLM Justification
    final = await generate_justification(scored)

    elapsed = time.time() - t0
    print(f"\n  Total pipeline time: {elapsed:.2f}s\n")
    print(json.dumps(final, indent=2))

async def main():
    await test_nominatim_connectivity()
    await test_full_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
