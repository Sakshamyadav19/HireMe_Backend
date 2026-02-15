import bcrypt
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user import User

# bcrypt only uses first 72 bytes
BCRYPT_MAX_PASSWORD_BYTES = 72

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > BCRYPT_MAX_PASSWORD_BYTES:
        encoded = encoded[:BCRYPT_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    encoded = plain.encode("utf-8")
    if len(encoded) > BCRYPT_MAX_PASSWORD_BYTES:
        encoded = encoded[:BCRYPT_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(encoded, hashed.encode("utf-8"))


def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode(
        {"user_id": user_id, "exp": expire},
        settings.JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def register_user(db: Session, name: str, email: str, password: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user


def get_user_by_id(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
