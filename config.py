import os
from pathlib import Path
import sys
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Safe loading: check for local .env or fallback cleanly to system os.environ
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "").strip()
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "").strip()
ADMIN_ID_RAW: str = os.environ.get("ADMIN_ID", "6125160021").strip()

# Clean, descriptive verification of required environment variables
missing_vars = []
if not BOT_TOKEN:
    missing_vars.append("BOT_TOKEN")
if not GEMINI_API_KEY:
    missing_vars.append("GEMINI_API_KEY")

if missing_vars:
    print(
        f"\n[CRITICAL ERROR] Missing required environment variable(s): {', '.join(missing_vars)}!\n"
        f"[RENDER DEPLOYMENT GUIDE] Go to Render Dashboard -> Web Service -> Environment -> Add Environment Variable\n"
        f"and set the missing values so the bot can operate properly.\n",
        file=sys.stderr,
    )

try:
    ADMIN_ID: int = int(ADMIN_ID_RAW)
except ValueError:
    print(
        f"[WARNING] Invalid ADMIN_ID '{ADMIN_ID_RAW}' in environment. Defaulting to 6125160021.",
        file=sys.stderr,
    )
    ADMIN_ID = 6125160021

DB_PATH: Path = BASE_DIR / "bot_database.db"

# Primary Gemini model and fallback models (fast models prioritized for 1-2s response time)
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
GEMINI_FALLBACK_MODELS = [
    GEMINI_MODEL,
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-2.5-flash",
]

# TolovAPI credentials
TOLOV_API_URL: str = "https://tolovapi.uz/api/"
DEFAULT_TOLOV_SHOP_ID: str = os.environ.get("TOLOV_SHOP_ID", "339").strip()
DEFAULT_TOLOV_SHOP_KEY: str = os.environ.get("TOLOV_SHOP_KEY", "cFpP7PdwqrDsVAdX").strip()

# Default Card Information
DEFAULT_CARD_NUMBER: str = os.environ.get("PAYMENT_CARD_NUMBER", "5614 6835 1125 2157").strip()
DEFAULT_CARD_OWNER: str = os.environ.get("PAYMENT_CARD_OWNER", "TolovAPI / Admin").strip()
DEFAULT_PROMO_CODE: str = "ENGLISH2026"

# Tariff durations in minutes
TARIFF_DURATIONS = {
    "free": 10,
    "standard_100k": 25,
    "pro_200k": 60,
}

# Target words slice per tariff
TARIFF_WORDS_COUNT = {
    "free": 5,
    "standard_100k": 12,
    "pro_200k": 25,
}
