import os

def _get_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got: {value!r}") from exc


API_ID = _get_int("API_ID", 0)
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

MONGO_URI = os.environ.get("MONGO_URI", "")
DB_NAME = os.environ.get("DB_NAME", "SilentXBotz")

WEB_SERVER = os.environ.get("WEB_SERVER", "True").lower() in ("true", "1", "t")
PORT = _get_int("PORT", 8080)
PING_INTERVAL = _get_int("PING_INTERVAL", 300)

TG_WORKERS = _get_int("TG_WORKERS", 4)

# Forwarding behaviour
BUFFER_DELAY = _get_int("BUFFER_DELAY", 4)
FORWARD_DELAY_SECONDS = float(os.environ.get("FORWARD_DELAY_SECONDS", "0.3"))
MAX_QUEUE_RETRIES = _get_int("MAX_QUEUE_RETRIES", 3)

# Your Koyeb/Heroku App Url
# Example : https://yorappurl.koyeb.app/
APP_URL = os.environ.get("APP_URL", None)
USER_SESSION_STRING = (
    os.environ.get("USER_SESSION_STRING")
    or os.environ.get("SESSION_STRING")
    or os.environ.get("BOT_SESSION")
    or ""
)

if API_ID <= 0:
    raise ValueError("API_ID is required and must be a positive integer")
if not API_HASH:
    raise ValueError("API_HASH is required")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required")
if not MONGO_URI:
    raise ValueError("MONGO_URI is required")
