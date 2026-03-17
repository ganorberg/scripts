import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "leads.db"

MILLION_VERIFIER_API_KEY = os.getenv("MILLION_VERIFIER_API_KEY", "")
INSTANTLY_API_KEY = os.getenv("INSTANTLY_API_KEY", "")

INSTANTLY_API_BASE = "https://api.instantly.ai/api/v2"
MILLION_VERIFIER_API_BASE = "https://api.millionverifier.com/api/v3/"
