import os
from dotenv import load_dotenv

load_dotenv()
# Load environment variables (assuming they are set in the environment or via python-dotenv before app startup)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LOCAL_API_BASE = os.getenv("LOCAL_API_BASE", "http://127.0.0.1:1234/v1/")

# Timeout and latency thresholds
LATENCY_LIMIT_MS = int(os.getenv("LATENCY_LIMIT_MS", "1000"))
GEMINI_TIMEOUT_SECONDS = 0.5 # 500ms
LOCAL_TIMEOUT_SECONDS = 2 # Local models might be slower

# Models
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "qwen2.5-coder-1.5b-instruct-mlx")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash-lite")

# General configuration
TARGET_CITY = os.getenv("TARGET_CITY", "")
