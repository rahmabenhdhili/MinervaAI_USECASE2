from fastapi import Request, HTTPException, status
from jose import jwt
from app.config import settings

def get_user_id_from_token(request: Request) -> str:
    """
    Extracts user_id from JWT token sent in Authorization header.
    Raises HTTP 401 if missing or invalid.
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token"
        )
    
    # Extract token string
    token = auth_header.split(" ")[1]

    try:
        # Decode JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")  # 'sub' holds user_id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
