import hashlib
import hmac
from datetime import UTC, datetime


def verify_telegram_auth(data: dict, bot_token: str, max_age_seconds: int = 86400) -> bool:
    check_hash = data.get("hash")
    if not check_hash:
        return False

    auth_date = data.get("auth_date")
    if auth_date is None:
        return False

    now = datetime.now(UTC).timestamp()
    if now - int(auth_date) > max_age_seconds:
        return False

    filtered = {k: v for k, v in data.items() if k != "hash"}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(filtered.items()))

    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(computed_hash, check_hash)
