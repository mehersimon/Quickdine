import os, uuid
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models import get_db, Restaurant

SECRET_KEY = os.getenv("SECRET_KEY", "quickdine-super-secret-key-change-in-prod")
ALGORITHM  = "HS256"
TOKEN_TTL  = 60 * 24  # 24 hours in minutes

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer  = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=TOKEN_TTL)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def gen_restaurant_id() -> str:
    return "resto_" + uuid.uuid4().hex[:8]


# --- Dependency: get current manager from JWT ---
def get_current_manager(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Restaurant:
    token = None
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    # Fallback: cookie
    if not token:
        token = request.cookies.get("qd_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token)
        rid = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    manager = db.query(Restaurant).filter(Restaurant.id == rid).first()
    if not manager:
        raise HTTPException(status_code=401, detail="Manager not found")
    return manager
