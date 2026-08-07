try:
    from postal.parser import parse_address
    HAS_POSTAL = True
except ImportError:
    HAS_POSTAL = False
from models.schemas import ParsedAddress

class ParserFallbackError(Exception):
    pass

def parse(raw_address: str) -> ParsedAddress:
    if not HAS_POSTAL:
        raise ParserFallbackError("libpostal library is not installed in this environment.")
        
    parsed = parse_address(raw_address)
    # libpostal returns a list of tuples: e.g. [('123', 'house_number'), ('main st', 'road')]
    result_dict = {k: v for v, k in parsed}
    
    # Mapping libpostal labels to our schema by combining available parts
    house_parts = [result_dict.get(k) for k in ['house', 'house_number', 'unit'] if k in result_dict]
    house_no = ", ".join(house_parts) if house_parts else None
    
    locality_parts = [result_dict.get(k) for k in ['road', 'suburb'] if k in result_dict]
    locality = ", ".join(locality_parts) if locality_parts else None
    
    city_parts = [result_dict.get(k) for k in ['city', 'city_district', 'state_district'] if k in result_dict]
    city = ", ".join(city_parts) if city_parts else None
    
    pincode = result_dict.get('postcode', None)
    landmark = result_dict.get('landmark', None)
    
    # Fallback criteria: If we have no pincode AND no locality/road AND no city, we consider the parse too weak.
    if not pincode and not locality and not city:
        raise ParserFallbackError("libpostal could not extract sufficient locality, city, or pincode.")
        
    return ParsedAddress(
        house_no=house_no,
        locality=locality,
        city=city,
        pincode=pincode,
        landmark=landmark,
        direction=None,
        language_detected="en" # libpostal operates internally mostly in latin script mapping
    )
