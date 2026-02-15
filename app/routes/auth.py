from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import settings
from app.middleware.auth import get_current_user_id
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    MessageResponse,
)
from app.services.auth import register_user, login_user, get_user_by_id, create_token, decode_token
from app.services.match_result_cache import clear_match_results_for_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _set_token_cookie(response: Response, token: str):
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=False,  # set True in production
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    user = register_user(db, body.name, body.email, body.password)
    token = create_token(user.id)
    _set_token_cookie(response, token)
    return AuthResponse.model_validate({"user": user})


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = login_user(db, body.email, body.password)
    token = create_token(user.id)
    _set_token_cookie(response, token)
    return AuthResponse.model_validate({"user": user})


@router.get("/me", response_model=AuthResponse)
def me(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, user_id)
    return AuthResponse.model_validate({"user": user})


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Clear session cookie and clear match result cache for this user."""
    token = request.cookies.get("token")
    if token:
        try:
            user_id = decode_token(token)
            clear_match_results_for_user(db, user_id)
        except HTTPException:
            pass
    response.delete_cookie(key="token", path="/")
    return {"message": "Logged out"}
