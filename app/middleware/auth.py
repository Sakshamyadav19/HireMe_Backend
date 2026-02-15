from fastapi import Request, HTTPException

from app.services.auth import decode_token


def get_current_user_id(request: Request) -> str:
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    return decode_token(token)
