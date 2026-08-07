from models.schemas import ParsedAddress
from typing import Tuple
from parsers import libpostal_parser, gemini_flash_parser, local_parser

async def parse_address(raw_address: str) -> Tuple[ParsedAddress, str]:
    """
    Attempts to parse the raw address using the 3-tier cascade.
    Returns the parsed address and the name of the parser that succeeded.
    """
    # Tier 1: libpostal (Fast C parser)
    try:
        parsed = libpostal_parser.parse(raw_address)
        return parsed, "libpostal"
    except Exception as e:
        print(f"[Tier 1 Fallback] libpostal failed: {e}")

    # Tier 2: Gemini Flash (LLM with structured output)
    try:
        parsed = await gemini_flash_parser.parse(raw_address)
        return parsed, "gemini_flash"
    except Exception as e:
        print(f"[Tier 2 Fallback] Gemini Flash failed: {e}")

    # Tier 3: Local Model via LM Studio (Final Fallback LLM)
    try:
        parsed = await local_parser.parse(raw_address)
        return parsed, "local_model"
    except Exception as e:
        print(f"[Tier 3 Fallback] Local Model failed: {e}")

    raise RuntimeError("All 3 parsing tiers failed.")
