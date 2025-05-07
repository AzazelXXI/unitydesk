import time
from fastapi import Request, HTTPException, status, Depends
from typing import Dict
import os
from threading import Lock

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_DEFAULT = int(os.getenv("RATE_LIMIT_DEFAULT", 100))
RATE_LIMIT_LOGIN = int(os.getenv("RATE_LIMIT_LOGIN", 10))
RATE_LIMIT_REGISTER = int(os.getenv("RATE_LIMIT_REGISTER", 5))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))

# In-memory store for demonstration (use Redis for production)
_rate_limit_store: Dict[str, list] = {}
_rate_limit_lock = Lock()


def rate_limiter(key_prefix: str, limit: int, window: int = RATE_LIMIT_WINDOW_SECONDS):
    def dependency(request: Request):
        if not RATE_LIMIT_ENABLED:
            return
        client_ip = request.client.host
        key = f"{key_prefix}:{client_ip}"
        now = time.time()
        with _rate_limit_lock:
            timestamps = _rate_limit_store.get(key, [])
            # Remove timestamps outside the window
            timestamps = [ts for ts in timestamps if now - ts < window]
            if len(timestamps) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again later.",
                )
            timestamps.append(now)
            _rate_limit_store[key] = timestamps

    return dependency


# Usage examples:
login_rate_limit = rate_limiter("login", RATE_LIMIT_LOGIN)
register_rate_limit = rate_limiter("register", RATE_LIMIT_REGISTER)
