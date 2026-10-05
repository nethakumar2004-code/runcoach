from datetime import timedelta
from typing import Optional
import hashlib
import hmac
import re

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app import config
from app.db import get_db
from app.models.user import User
from app.timeutils import utcnow

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer()

_LEGACY_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def is_legacy_hash(hashed_password: str) -> bool:
    """Accounts created before the bcrypt switch store an unsalted SHA-256 hex digest."""
    return bool(_LEGACY_SHA256.match(hashed_password or ""))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    if is_legacy_hash(hashed_password):
        legacy = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, hashed_password)
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:  # bcrypt limit; signup never allows longer passwords
        return False
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)


def _get_dev_user(db: Session) -> User:
    test_user = db.query(User).filter(User.email == "test@example.com").first()
    if not test_user:
        test_user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            name="Test User",
            experience_level="intermediate"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    return test_user


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Development bypass for the mobile debug screen. Only active when RUNCOACH_DEV_MODE is on,
    # otherwise anyone could log in as the test user without a password.
    if config.DEV_MODE and credentials.credentials == "dev-token":
        return _get_dev_user(db)

    try:
        payload = jwt.decode(credentials.credentials, config.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if (current_user.email or "").lower() not in config.ADMIN_EMAILS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can do this")
    return current_user
