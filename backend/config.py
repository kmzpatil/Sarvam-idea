import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env from root or parent directory
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Read API keys strictly from environment variables
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
CARTO_API_KEY = os.environ.get("CARTO_API_KEY", "") or os.environ.get("VITE_CARTO_KEY", "")

# Base URLs
SARVAM_BASE_URL = "https://api.sarvam.ai"
SARVAM_DOC_AI_URL = "https://api.sarvam.ai/doc-ai/v1"

# Supported Indian Languages
SUPPORTED_LANGUAGES = {
    "hi-IN": {"name": "Hindi", "native": "हिन्दी"},
    "bn-IN": {"name": "Bengali", "native": "বাংলা"},
    "ta-IN": {"name": "Tamil", "native": "தமிழ்"},
    "te-IN": {"name": "Telugu", "native": "తెలుగు"},
    "mr-IN": {"name": "Marathi", "native": "मराठी"},
    "gu-IN": {"name": "Gujarati", "native": "ગુજરાતી"},
    "kn-IN": {"name": "Kannada", "native": "ಕನ್ನಡ"},
    "ml-IN": {"name": "Malayalam", "native": "മലയാളം"},
    "pa-IN": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ"},
    "od-IN": {"name": "Odia", "native": "ଓଡ଼ିଆ"},
    "en-IN": {"name": "English", "native": "English"},
}

DEFAULT_LANGUAGE = "hi-IN"
DEFAULT_MODEL = "sarvam-105b"
