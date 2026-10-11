import os
from pathlib import Path
from dotenv import load_dotenv

# Locate backend root and load .env file
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()  # fallback to current working directory

# API Credentials
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "").strip()
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "").strip()
DEFAULT_PROVIDER = os.getenv("AI_PROVIDER", "auto").strip().lower()

# Server Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Upload Constraints
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
MAX_IMAGE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def get_stability_key() -> str:
    """Safely fetch current Stability API key from env or .env file."""
    if "STABILITY_API_KEY" in os.environ:
        return os.environ["STABILITY_API_KEY"].strip()
    load_dotenv(BACKEND_DIR / ".env")
    return os.getenv("STABILITY_API_KEY", "").strip()

def get_replicate_token() -> str:
    """Safely fetch current Replicate token from env or .env file."""
    if "REPLICATE_API_TOKEN" in os.environ:
        return os.environ["REPLICATE_API_TOKEN"].strip()
    load_dotenv(BACKEND_DIR / ".env")
    return os.getenv("REPLICATE_API_TOKEN", "").strip()


def get_active_provider() -> str:
    """
    Detect default AI provider.
    Returns 'auto' (Stability with auto-fallback to Free AI),
    or explicit user-selected provider.
    """
    stab = get_stability_key()
    repl = get_replicate_token()
    env_provider = os.getenv("AI_PROVIDER", "").strip().lower()

    if env_provider in {"auto", "free", "demo", "stability", "replicate"}:
        return env_provider

    if stab:
        return "auto"
    elif repl:
        return "replicate"
    return "free"

def is_ai_configured() -> bool:
    """Return True since Free Fashion AI and Demo engines are always ready."""
    return True

def get_available_providers() -> list[str]:
    """Returns list of all available engines."""
    providers = ["auto", "free", "demo"]
    if get_stability_key():
        providers.append("stability")
    if get_replicate_token():
        providers.append("replicate")
    return providers
