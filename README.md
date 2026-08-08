# Pata AI - Address Intelligence Engine

Pata AI is an Evidence-Driven Address Intelligence Engine tailored specifically for last-mile delivery in India. The system handles the complexities of Indian address formats—such as colloquial area names, localized landmarks, mixed scripts, and missing postal codes—by executing a 3-tier address parsing cascade alongside evidence-based geo-matching and automated confidence scoring.

---
<img width="2720" height="1440" alt="pata_mvp_architecture" src="https://github.com/user-attachments/assets/eeb13221-f16e-4bec-99dc-cbc4f2dc5db5" />


## System Architecture and Workflow

The system processes incoming unstructured address strings through a sequential 4-step pipeline managed by the FastAPI backend and rendered by the React frontend:

```
[Raw Address Input]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ Step 1: 3-Tier Address Parsing Cascade                 │
│ 1. libpostal (Primary C-based Parser - Optional)       │
│ 2. Gemini Flash (Secondary Indic-Aware LLM Fallback)   │
│ 3. Local Model (LM Studio - Tertiary LLM Fallback)     │
└────────────────────────┬───────────────────────────────┘
                         │ Parsed Components
                         ▼
┌────────────────────────────────────────────────────────┐
│ Step 2: Ground Truth & Landmark Geocoding              │
│ - Dynamic OSM Pincode Boundary Fetching            │
│ - Nominatim POI Search within Strict Geofence      │
└────────────────────────┬───────────────────────────────┘
                         │ Matched Geo Data
                         ▼
┌────────────────────────────────────────────────────────┐
│ Step 3: Confidence Scoring & Evidence Justification   │
│ - Mathematical Confidence Scoring Formula              │
│ - LLM Evidence Justification Generation                │
└────────────────────────┬───────────────────────────────┘
                         │ Validated Payload
                         ▼
┌────────────────────────────────────────────────────────┐
│ Step 4: Frontend UI & Map Rendering                    │
│ - Visual Comparison: Raw Pin vs. High-Confidence Pin    │
│ - Driver-facing Evidence Card & Audit Banner           │
└────────────────────────────────────────────────────────┘
```

### Detailed Execution Flow
<img width="1408" height="768" alt="workflow" src="https://github.com/user-attachments/assets/49dbf697-b363-4482-9ae3-61d0e88b46bf" />


1. **Step 1: 3-Tier Address Parsing Cascade (`backend/parsers/`)**
   - **Primary (`libpostal_parser.py`):** Fast C-based statistical parser used as the first line of defense to extract structural elements (house numbers, road, area, city, pincode). *Note: This tier gracefully skips itself if libpostal is not installed (e.g., in our fast Docker setup).*
   - **Secondary (`gemini_flash_parser.py`):** Invoked if `libpostal` parsing fails or is skipped. Utilizes Google Gemini Flash for Indic-aware contextual parsing. **It automatically translates regional languages (Telugu, Hindi, etc.) into English.**
   - **Tertiary (`local_parser.py`):** High-reliability local LLM fallback (e.g., running via LM Studio) triggered if secondary parsing fails. Also enforces English translation.
   - **Orchestration (`parser_orchestrator.py`):** Controls the fallback cascade logic and ensures graceful degradation.

2. **Step 2: Ground Truth & Landmark Geocoding (`backend/matcher/`)**
   - **Pincode Boundary Fetching (`pincode_db.py` & `osm_client.py`):** First checks Nominatim to dynamically retrieve the exact real-world polygonal bounding box for the given pincode. Falls back to a local `pincodes_clean.csv` if the API fails.
   - **Landmark Geocoding (`geocoder_engine.py` & `osm_client.py`):** Cross-references extracted area and landmark entities against OpenStreetMap (OSM) via the Nominatim API, strictly bounded (geofenced) by the exact pincode boundaries to ensure it never returns results from neighboring cities.

3. **Step 3: Confidence Scoring & Evidence Justification (`backend/self_check/`)**
   - **Confidence Scoring (`confidence_scorer.py`):** Calculates a deterministic confidence score based on parsing completeness, pincode validity, landmark proximity, and spatial delta.
   - **Evidence Generation (`evidence_agent.py`):** Generates concise, driver-facing justification text explaining the rationale behind the location match and highlighting key matched landmarks.

4. **Step 4: Delivery Interface Rendering (`frontend/`)**
   - React application sends raw address text via `api/client.js` to the FastAPI `/geocode` endpoint.
   - Map component (`MapView.jsx`) plots both the original raw input coordinates and the validated high-confidence location pin.
   - UI presents the audit log (`AuditBanner.jsx`) and evidence explanation (`EvidenceCard.jsx`).

---

## Project Structure

```
PATA-T001/
│
├── docker-compose.yml           # Runs backend (FastAPI + libpostal binaries) and frontend
├── README.md                    # Setup instructions and documentation
│
├── docs/                        # Hackathon Deliverables
│   ├── architecture_diagram.png # Architecture diagram of the 3-tier parser and MVP
│   ├── business_pitch.pdf       # Problem, solution, value, cost-per-transaction, roadmap
│   └── test_addresses.csv       # Messy test addresses with mixed scripts and landmarks
│
├── backend/                     # FastAPI Geocoding Engine
│   ├── requirements.txt         # fastapi, postal, google-genai, openai, pandas, httpx
│   ├── .env.example             # GEMINI_API_KEY, NVIDIA_NIM_API_KEY
│   ├── main.py                  # POST /geocode entry point (orchestrates Steps 1–4)
│   │
│   ├── parsers/                 # STEP 1: 3-Tier Address Parser Cascade
│   │   ├── __init__.py
│   │   ├── parser_orchestrator.py # Manages fallback: libpostal -> Gemini Flash -> Local Model
│   │   ├── libpostal_parser.py    # Primary C-based parser
│   │   ├── gemini_flash_parser.py # Secondary Indic-aware LLM fallback (with translation)
│   │   └── local_parser.py        # Tertiary Local LLM fallback via LM Studio
│   │
│   ├── matcher/                 # STEP 2: Ground Truth & Landmark Geocoding
│   │   ├── __init__.py
│   │   ├── pincode_db.py          # Fallback loader for pincodes_clean.csv
│   │   ├── geocoder_engine.py     # Uses Dynamic Boundaries + OSM Landmark Search
│   │   └── osm_client.py          # Async client for Nominatim POI and Boundary lookups
│   │
│   ├── self_check/              # STEP 3: Confidence Scoring & Evidence Justification
│   │   ├── __init__.py
│   │   ├── confidence_scorer.py   # Mathematical evidence scoring formula
│   │   └── evidence_agent.py      # LLM call to generate driver-facing justification text
│   │
│   ├── data/
│   │   ├── pincodes_clean.csv     # Kaggle All-India Pincode Directory CSV (Fallback)
│   │   └── test_addresses.json    # Handcrafted evaluation dataset
│   │
│   ├── models/
│   │   └── schemas.py             # Pydantic schemas for requests and responses
│   │
│   └── utils/
│       ├── __init__.py
│       ├── latency_tracker.py     # Middleware & timing utilities for sub-500ms enforcement
│       ├── cost_tracker.py        # Token & execution cost logger
│       └── privacy.py             # Memory scrubbing and address sanitization hooks
│
└── frontend/                    # Interactive Delivery UI MVP
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── App.jsx                # Main user journey MVP demonstrating the full flow
    │   ├── components/
    │   │   ├── AddressInput.jsx   # Input field for raw messy text
    │   │   ├── MapView.jsx        # Displays high-confidence pin vs. raw input pin
    │   │   ├── EvidenceCard.jsx   # Renders LLM justification & matched landmark
    │   │   └── AuditBanner.jsx    # Displays original messy string alongside correction
    │   └── api/
    │       └── client.js          # Fetch payload to FastAPI `/geocode` endpoint
```

---

## Setup Instructions

### 1. Prerequisites

- **libpostal C Library:** Ensure the `libpostal` C library and data files are installed on your system.
- **Python:** Version 3.9 or higher.
- **Node.js:** Version 18 or higher.

---

### 2. Backend Setup

The backend is built with FastAPI and runs all parsing, geocoding, and confidence scoring logic.

1. **Create and Activate a Virtual Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python Dependencies:**
   Since `libpostal` is installed on your system, the Python bindings (`postal`) will compile against the C library during this step:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy the example environment file and fill in your API keys:
   ```bash
   cp backend/.env.example backend/.env
   ```
   Set your API keys inside `backend/.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   LOCAL_API_BASE=http://127.0.0.1:1234/v1/
   LOCAL_MODEL=qwen2.5-coder-1.5b-instruct-mlx
   ```

4. **Run the Backend Server:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   The backend will be available at `http://localhost:8000`.

---

### 3. Frontend Setup

The frontend is an interactive UI built with React and Vite.

1. **Install Node Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Run the Development Server:**
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`.

---

### 4. Running with Docker Compose

We provide a highly-optimized, lightweight default Docker setup that skips the heavy 2GB `libpostal` C-library installation. It relies purely on the Gemini and Local LLM tiers for parsing, making builds blazing fast!

```bash
docker-compose up --build
```

#### Running with full libpostal (Optional)
If you require the Tier 1 C-parser inside Docker, we preserved the original configuration files:
```bash
cd backend
docker build -f Dockerfile.full -t pata-backend-full .
```

---

## API Specification

### POST `/geocode`

#### Request Body
```json
{
  "address": "Flat 302, Sai Residency, near Post Office, Madhapur, Hyderabad 500081"
}
```

#### Response Body
```json
{
  "parsed_address": {
    "house_number": "Flat 302",
    "building": "Sai Residency",
    "landmark": "near Post Office",
    "area": "Madhapur",
    "city": "Hyderabad",
    "pincode": "500081",
    "parser_used": "libpostal"
  },
  "geocoding": {
    "latitude": 17.4486,
    "longitude": 78.3908,
    "matched_pincode": "500081",
    "matched_area": "Madhapur",
    "matched_landmark": "Madhapur Post Office"
  },
  "validation": {
    "confidence_score": 0.94,
    "is_high_confidence": true,
    "evidence_justification": "Address matched to Madhapur area (Pincode 500081). Landmark 'Post Office' verified via OSM POI reference data within 120m radius."
  },
  "metrics": {
    "latency_ms": 184,
    "cost_usd": 0.00002
  }
}
```
