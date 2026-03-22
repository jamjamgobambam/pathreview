from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
import structlog

from core.security import decode_access_token
from core.database import get_db
from core.models.user import User

log = structlog.get_logger()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db),
) -> User:
    """
    Decode JWT token and return authenticated user.
    Raises 401 if token is invalid, expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        exp = payload.get("exp")

        if user_id is None:
            raise credentials_exception

        # Check token expiry
        if exp is not None:
            if datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    except Exception as exc:
        log.error("token_decode_failed", error=str(exc))
        raise credentials_exception

    # Query user from database
    try:
        user = await db.query(User).filter(User.id == user_id).first()
    except Exception as exc:
        log.error("user_lookup_failed", user_id=user_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )

    if user is None:
        raise credentials_exception

    return user
