import hmac
import hashlib
import time
from config import settings


def generate_signature(method: str, path: str, query_string: str = "", body: str = "") -> dict:
    timestamp = str(int(time.time()))
    message = method + timestamp + path + query_string + body
    signature = hmac.new(
        settings.delta_api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return {
        "api-key": settings.delta_api_key,
        "timestamp": timestamp,
        "signature": signature,
        "Content-Type": "application/json",
    }
