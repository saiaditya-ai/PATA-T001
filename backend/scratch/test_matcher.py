import asyncio
import json
import os
import sys

# Add backend to path so we can import utils and matcher
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from matcher.location_matcher import resolve_vague_address

async def main():
    sample_json = {
      "house_no": "flat 202",
      "locality": "opp ganesh temple madhapur hyd",
      "city": None,
      "pincode": "500081",
      "landmark": "hitech city",
      "direction": None,
      "language_detected": "en"
    }
    
    print("Testing resolve_vague_address with:")
    print(json.dumps(sample_json, indent=2))
    
    result = await resolve_vague_address(sample_json)
    
    print("\nResult:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
