import asyncio
from typing import List, Dict, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
import os
import sys

# Adjust path so we can import from config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY, GEMINI_TIMEOUT_SECONDS, GEMINI_MODEL_NAME

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class EvaluatedLandmark(BaseModel):
    selected_index: int
    reason: str

SYSTEM_INSTRUCTION = """
You are an expert location evaluator. Your task is to look at a user's address and a list of possible landmark results retrieved from a map database.
Identify which of the possible landmarks is the best match for the user's intended locality/landmark.

Return a JSON object containing:
- "selected_index": The integer index (0-based) of the best matching landmark in the list. If NONE of the landmarks are a reasonable match, return -1.
- "reason": A brief explanation of why you selected this index (or why you selected -1).
"""

async def _evaluate_landmarks_call(parsed_address: Dict[str, Any], candidates: List[Dict[str, Any]]) -> EvaluatedLandmark:
    if not candidates:
        return EvaluatedLandmark(selected_index=-1, reason="No candidates provided.")
    
    # Construct the prompt
    candidates_text = ""
    for i, c in enumerate(candidates):
        candidates_text += f"[{i}] Name: {c.get('name')} | Address details: {c.get('address')}\n"
    
    prompt = f"""
    User's Parsed Address: {parsed_address}
    
    Possible Landmarks from Map Database:
    {candidates_text}
    """

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=EvaluatedLandmark,
            temperature=0.0
        ),
    )
    return response.parsed

async def evaluate_landmarks(parsed_address: Dict[str, Any], candidates: List[Dict[str, Any]]) -> int:
    """
    Evaluates a list of landmark candidates against the parsed address using Gemini.
    Returns the index of the best candidate, or -1 if none match.
    """
    if not candidates:
        return -1
        
    if not client:
        # Fallback if no API key is provided
        print("Warning: Gemini API key not set. Skipping AI landmark evaluation.")
        return 0
        
    try:
        # Use a slightly longer timeout for evaluation, as it reads multiple candidates
        timeout = max(GEMINI_TIMEOUT_SECONDS, 2.0)
        result = await asyncio.wait_for(_evaluate_landmarks_call(parsed_address, candidates), timeout=timeout)
        print(f"Gemini selected index {result.selected_index} for reason: {result.reason}")
        return result.selected_index
    except asyncio.TimeoutError:
        print("Gemini landmark evaluation timed out.")
        return 0
    except Exception as e:
        print(f"Gemini landmark evaluation failed: {e}")
        return 0
