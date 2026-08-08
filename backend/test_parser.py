import asyncio
import json
from parsers.parser_orchestrator import parse_address

async def main():
    print("=========================================")
    print("Pata AI - Parser Cascade Test")
    print("=========================================\n")

    addresses = [
        # Clean english address - will be caught by libpostal
        "42-2/1-206/1A, 3rd right, 5th line, Devinagar, Vijayawada, 520003"
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
