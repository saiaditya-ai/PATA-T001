# Pata AI - Address Intelligence Engine

**Pata** is an Evidence-Driven Address Intelligence Engine tailored for last-mile delivery in India. It implements a 3-Tier address parsing cascade (libpostal -> Gemini Flash -> NVIDIA NIM) along with evidence-based geo-matching.

## Setup Instructions

### 1. Prerequisites
- **libpostal**: Ensure the `libpostal` C library is already installed on your system.
- **Python 3.9+**
- **Node.js 18+**

### 2. Backend Setup

The backend is built with FastAPI and runs all parsing and geocoding logic.

1. **Create and Activate a Virtual Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python Dependencies:**
   Since `libpostal` is installed on your system, the Python bindings (`postal`) will compile against it during this step.
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy the example environment file and fill in your API keys:
   ```bash
   cp backend/.env.example backend/.env
   ```
   Add your `GEMINI_API_KEY` and `NVIDIA_NIM_API_KEY` inside `backend/.env`.

4. **Run the Backend Server:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

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

### 4. Running with Docker Compose
If you prefer running both services together via Docker:
```bash
docker-compose up --build
```
