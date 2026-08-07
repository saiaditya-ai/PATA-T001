import asyncio
import json
from parsers.parser_orchestrator import parse_address

async def main():
    print("=========================================")
    print("Pata AI - Parser Cascade Test")
    print("=========================================\n")

    addresses = [
        # Clean english address - will be caught by libpostal
        "Flat 202, opp Ganesh temple, madhapur, hyd, 500081",
        
        # Regional / unstructured address - will fallback to Gemini/NIM
        "మధురవాడ, విశాఖపట్నం, 530041 దగ్గర"
    ]

    for addr in addresses:
        print(f"--- Testing Address: {addr} ---")
        try:
            parsed_result, source = await parse_address(addr)
            print(f"Successfully parsed by: {source}")
            print(json.dumps(parsed_result.model_dump(), indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Orchestrator failed: {e}")
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
