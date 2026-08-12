"""
All the "knobs" for the backend live here. If you want to change the
LLM model, swap databases, or point at a different Groq endpoint,
this is the only file you should need to touch.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Groq / LLM settings -----------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Primary model for extraction/correction (fast + cheap, good for structured JSON)
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "gemma2-9b-it")

# Optional stronger model you can switch to for the risk-assessment step
# if you want better reasoning there. Same model works fine too.
RISK_MODEL = os.getenv("RISK_MODEL", "llama-3.3-70b-versatile")

# --- Database ------------------------------------------------------------
# Defaults to a local Postgres. Swap this string for a MySQL URL if you'd
# rather use MySQL, e.g. "mysql+pymysql://user:pass@localhost/aivoa"
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aivoa"
)

# --- App -------------------------------------------------------------
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
