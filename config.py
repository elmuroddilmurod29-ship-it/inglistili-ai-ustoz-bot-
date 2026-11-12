import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "6125160021").strip()
try:
    ADMIN_ID: int = int(ADMIN_ID_RAW)
except ValueError:
    ADMIN_ID: int = 6125160021

DB_PATH: Path = BASE_DIR / "bot_database.db"

# Primary Gemini model and fallback models (fast models prioritized for 1-2s response time)
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
GEMINI_FALLBACK_MODELS = [
    GEMINI_MODEL,
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-2.5-flash",
]

# TolovAPI credentials
TOLOV_API_URL: str = "https://tolovapi.uz/api/"
DEFAULT_TOLOV_SHOP_ID: str = "339"
DEFAULT_TOLOV_SHOP_KEY: str = "cFpP7PdwqrDsVAdX"

# Default Card Information
DEFAULT_CARD_NUMBER: str = "5614 6835 1125 2157"
DEFAULT_CARD_OWNER: str = "TolovAPI / Admin"
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
