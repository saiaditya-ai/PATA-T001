from typing import Optional, List, Tuple
from pydantic import BaseModel

class AddressRequest(BaseModel):
    raw_address: str

class ParsedAddress(BaseModel):
    house_no: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    landmark: Optional[str] = None
    direction: Optional[str] = None
    language_detected: Optional[str] = None

class EvidencePayload(BaseModel):
    pincode_matched: bool
    poi_matched: str
    distance_meters: float
    verification_steps: List[str]

class AddressResponse(BaseModel):
    status: str
    confidence_score: float
    confidence_level: str
    coordinates: Tuple[float, float]
    parsed_structure: ParsedAddress
    evidence: EvidencePayload
    justification_text: str
    latency_ms: float
    original_address: str
