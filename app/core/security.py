from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config import settings

def hash_password(password:str)->str:
    hashed_pass=bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12))
    return hashed_pass.decode("utf-8")

def verify_password(password:str,hashed_password:str)->bool:
    is_match=bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8"))
    return is_match

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MIN)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
