import httpx
from typing import List, Dict, Any, Optional, Tuple

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "PataAI/1.0 (address-intelligence-engine)"}

# Keyword → (Nominatim tag type, tag value)
LANDMARK_TYPE_MAP: List[Tuple[str, str, str]] = [
    # keyword        tag_key    tag_value
    ("hospital",    "amenity", "hospital"),
    ("clinic",      "amenity", "clinic"),
    ("pharmacy",    "amenity", "pharmacy"),
    ("dispensary",  "amenity", "pharmacy"),
    ("school",      "amenity", "school"),
    ("college",     "amenity", "college"),
    ("university",  "amenity", "university"),
    ("institute",   "amenity", "college"),
    ("temple",      "amenity", "place_of_worship"),
    ("mandir",      "amenity", "place_of_worship"),
    ("mosque",      "amenity", "place_of_worship"),
    ("masjid",      "amenity", "place_of_worship"),
    ("church",      "amenity", "place_of_worship"),
    ("bank",        "amenity", "bank"),
    ("atm",         "amenity", "atm"),
    ("police",      "amenity", "police"),
    ("post office", "amenity", "post_office"),
    ("petrol",      "amenity", "fuel"),
    ("fuel",        "amenity", "fuel"),
    ("restaurant",  "amenity", "restaurant"),
    ("hotel",       "amenity", "hotel"),
    ("cinema",      "amenity", "cinema"),
    ("theatre",     "amenity", "theatre"),
    ("park",        "leisure", "park"),
    ("garden",      "leisure", "garden"),
    ("bakery",      "shop",    "bakery"),
    ("bakers",      "shop",    "bakery"),
    ("supermarket", "shop",    "supermarket"),
    ("market",      "shop",    "marketplace"),
    ("mall",        "shop",    "mall"),
    ("salon",       "shop",    "hairdresser"),
]


def detect_landmark_type(term: str) -> Optional[Tuple[str, str]]:
    """
    Returns (tag_key, tag_value) for Nominatim if the term contains a known
    landmark-type keyword, else returns None.
    """
    lower = term.lower()
    for keyword, tag_key, tag_value in LANDMARK_TYPE_MAP:
        if keyword in lower:
            return (tag_key, tag_value)
    return None


def _parse_elements(data: list) -> List[Dict[str, Any]]:
    results = []
    for el in data:
        results.append({
            "name": el.get("display_name", "Unknown"),
            "type": el.get("type", "unknown"),
            "osm_type": el.get("osm_type"),
            "coordinates": {
                "latitude": float(el.get("lat", 0)),
                "longitude": float(el.get("lon", 0))
            },
            "address": el.get("address", {})
        })
    return results

async def get_pincode_boundary(pincode: str) -> Optional[Tuple[str, float, float]]:
    """
    Queries Nominatim for the pincode to get its exact bounding box and center coordinates.
    Returns (viewbox_str, lat, lon) if found, else None.
    viewbox is formatted as "lon1,lat1,lon2,lat2".
    """
    if not pincode:
        return None
    
    async with httpx.AsyncClient(timeout=5.0, headers=HEADERS) as client:
        try:
            # Add 'India' to disambiguate from foreign postal codes
            r = await client.get(NOMINATIM_URL, params={
                "q": f"{pincode}, India",
                "format": "json",
                "limit": 1
            })
            r.raise_for_status()
            data = r.json()
            if data and len(data) > 0:
                el = data[0]
                bb = el.get("boundingbox")
                if bb and len(bb) == 4:
                    # boundingbox is [lat_min, lat_max, lon_min, lon_max]
                    # viewbox for Nominatim needs: lon1,lat1,lon2,lat2
                    lat_min, lat_max, lon_min, lon_max = bb
                    viewbox = f"{lon_min},{lat_max},{lon_max},{lat_min}"
                    lat = float(el.get("lat", 0.0))
                    lon = float(el.get("lon", 0.0))
                    if lat and lon:
                        return viewbox, lat, lon
        except Exception as e:
            print(f"Failed to fetch pincode boundary for {pincode}: {e}")
            
    return None


async def search_landmarks_near_coordinates(
    search_term: str, lat: float, lon: float, radius: int = 1000, viewbox_str: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Smart landmark search strategy:
      1. Direct name search (bounded viewbox).
      2. If 0 results: detect landmark type keyword and search by type in area.
      3. If 0 results: unbounded name search with viewbox preference.
    """
    if not search_term:
        return []

    # Viewbox from radius (1 deg ~ 111km)
    if viewbox_str:
        viewbox = viewbox_str
    else:
        delta = (radius / 1000) / 111.0
        viewbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"

    async with httpx.AsyncClient(timeout=5.0, headers=HEADERS) as client:

        # --- Pass 1: Exact name, bounded ---
        params = {
            "q": search_term,
            "format": "json",
            "viewbox": viewbox,
            "bounded": 1,
            "limit": 10,
            "addressdetails": 1,
        }
        try:
            r = await client.get(NOMINATIM_URL, params=params)
            r.raise_for_status()
            data = r.json()
            if data:
                return _parse_elements(data)
        except Exception as e:
            print(f"OSM pass 1 failed: {e}")

        # --- Pass 2: Type-only search in the area ---
        landmark_type = detect_landmark_type(search_term)
        if landmark_type:
            tag_key, tag_value = landmark_type
            params = {
                tag_key: tag_value,
                "format": "json",
                "viewbox": viewbox,
                "bounded": 1,
                "limit": 10,
                "addressdetails": 1,
            }
            try:
                r = await client.get(NOMINATIM_URL, params=params)
                r.raise_for_status()
                data = r.json()
                if data:
                    return _parse_elements(data)
            except Exception as e:
                print(f"OSM pass 2 (type search) failed: {e}")

        # --- Pass 3: Name search, strictly bounded ---
        # Note: Set bounded=1 to strictly enforce the radius to prevent jumping to other states.
        params = {
            "q": search_term,
            "format": "json",
            "viewbox": viewbox,
            "bounded": 1,
            "limit": 5,
            "addressdetails": 1,
        }
        try:
            r = await client.get(NOMINATIM_URL, params=params)
            r.raise_for_status()
            data = r.json()
            if data:
                return _parse_elements(data)
        except Exception as e:
            print(f"OSM pass 3 failed: {e}")

    return []

async def search_structured_address(
    street: str, city: str, postalcode: str, lat: float, lon: float, radius: int = 1000
) -> List[Dict[str, Any]]:
    """
    Performs a structured search using Nominatim's structured query parameters.
    This is best for pinpointing exact addresses with house numbers.
    """
    if not street:
        return []

    # Viewbox from radius
    delta = (radius / 1000) / 111.0
    viewbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"

    async with httpx.AsyncClient(timeout=5.0, headers=HEADERS) as client:
        params = {
            "street": street,
            "format": "json",
            "viewbox": viewbox,
            "bounded": 1,
            "limit": 5,
            "addressdetails": 1,
        }
        if city:
            params["city"] = city
        if postalcode:
            params["postalcode"] = postalcode

        try:
            r = await client.get(NOMINATIM_URL, params=params)
            r.raise_for_status()
            data = r.json()
            if data:
                return _parse_elements(data)
        except Exception as e:
            print(f"OSM structured search failed: {e}")

    return []
