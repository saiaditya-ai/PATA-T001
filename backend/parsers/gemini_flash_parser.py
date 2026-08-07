import asyncio
from google import genai
from google.genai import types
from models.schemas import ParsedAddress
from config import GEMINI_API_KEY, GEMINI_TIMEOUT_SECONDS, GEMINI_MODEL_NAME

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_INSTRUCTION = """
You are an expert Indian address parser. Extract the following fields from messy addresses into a strict JSON structure.
Fields: house_no, locality, city, pincode (6 digits), landmark, direction, language_detected (e.g. 'en', 'hi', 'te', 'ta').

Examples:
Input: "Flat 202, opp Ganesh temple, madhapur, hyd 500081"
Output: {"house_no": "Flat 202", "locality": "madhapur", "city": "hyd", "pincode": "500081", "landmark": "Ganesh temple", "direction": "opp", "language_detected": "en"}

Input: "మధురవాడ, విశాఖపట్నం, 530041 దగ్గర"
Output: {"house_no": null, "locality": "మధురవాడ", "city": "విశాఖపట్నం", "pincode": "530041", "landmark": null, "direction": "దగ్గర", "language_detected": "te"}
"""

async def _call_gemini(raw_address: str) -> ParsedAddress:
    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=raw_address,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ParsedAddress,
            temperature=0.0
        ),
    )
    return response.parsed

async def parse(raw_address: str) -> ParsedAddress:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    try:
        # Wrap the API call with an asyncio timeout
        return await asyncio.wait_for(_call_gemini(raw_address), timeout=GEMINI_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise TimeoutError("Gemini parser timed out.")
    except Exception as e:
        raise Exception(f"Gemini parser failed: {str(e)}")
