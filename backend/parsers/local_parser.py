import asyncio
import json
from openai import AsyncOpenAI
from models.schemas import ParsedAddress
from config import LOCAL_API_BASE, LOCAL_TIMEOUT_SECONDS, LOCAL_MODEL

# LM Studio doesn't require a real API key, but the OpenAI client expects a non-empty string.
client = AsyncOpenAI(
    base_url=LOCAL_API_BASE,
    api_key="lm-studio"
)

SYSTEM_PROMPT = """
You are an expert Indian address parser. Extract the following fields from messy addresses into a strict JSON structure.
Fields: house_no, locality, city, pincode, landmark, direction, language_detected.
Schema: {"house_no": string|null, "locality": string|null, "city": string|null, "pincode": string|null, "landmark": string|null, "direction": string|null, "language_detected": string|null}
IMPORTANT: Output ONLY the JSON object. Do not output any conversational text before or after the JSON. Your response must start with '{' and end with '}'.
"""

async def _call_local(raw_address: str) -> ParsedAddress:
    response = await client.chat.completions.create(
        model=LOCAL_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_address}
        ],
        temperature=0.0,
        max_tokens=500
    )
    content = response.choices[0].message.content
    try:
        # Find the first '{' and last '}' to extract just the JSON part
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            content = content[start_idx:end_idx+1]
        
        data = json.loads(content)
        return ParsedAddress(**data)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse Local Model response as JSON. Content: {content}")

async def parse(raw_address: str) -> ParsedAddress:
    try:
        return await asyncio.wait_for(_call_local(raw_address), timeout=LOCAL_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise TimeoutError("Local Model parser timed out.")
    except Exception as e:
        raise Exception(f"Local Model parser failed: {str(e)}")
