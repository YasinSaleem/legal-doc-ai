# src/config.py
"""
Configuration module
--------------------
Handles environment variables, folder paths, and global constants.
Ensures all key directories exist before the rest of the system runs.
"""

import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# === ENVIRONMENT VARIABLES ===
try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
except KeyError:
    raise KeyError("❌ GEMINI_API_KEY not found. Did you set it in your .env file?")

# === DIRECTORY CONSTANTS ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
BASE_TEMPLATE_DIR = os.path.join(BASE_DIR, "base_templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DOC_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "docs")
METADATA_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "metadata")
SCHEMA_DIR = os.path.join(BASE_DIR, "schemas")
STYLE_DIR = os.path.join(BASE_DIR, "styles")
WORKING_DIR = os.path.join(BASE_DIR, "working")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# === GLOBAL SETTINGS ===
LOG_FILE = os.path.join(LOG_DIR, "activity.log")
DEFAULT_MODEL = "gemini-2.0-flash"
SUPPORTED_DOC_TYPES = ["NDA", "Offer_Letter", "Contract", "MOU", "IP_Agreement"]

def ensure_directories_exist():
    """Create required directories if they don't exist."""
    for path in [
        TEMPLATE_DIR,
        BASE_TEMPLATE_DIR,
        OUTPUT_DIR,
        DOC_OUTPUT_DIR,
        METADATA_OUTPUT_DIR,
        SCHEMA_DIR,
        STYLE_DIR,
        WORKING_DIR,
        LOG_DIR,
    ]:
        os.makedirs(path, exist_ok=True)

# Ensure folder structure is ready at import time
ensure_directories_exist()

# === DEBUG PRINT (optional) ===
# if __name__ == "__main__":
#     print("✅ Configuration loaded successfully.")
#     print(f"Base directory: {BASE_DIR}")
#     print(f"Gemini model: {DEFAULT_MODEL}")
#     print(f"Output directory: {OUTPUT_DIR}")


# Add this to your config.py file

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi', 
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ar': 'Arabic',
    'zh': 'Chinese'
}

def get_supported_languages():
    """Return dictionary of supported languages"""
    return SUPPORTED_LANGUAGES

