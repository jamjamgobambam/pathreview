from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import structlog

from api.schemas.user import UserCreate, UserResponse, Token
from core.database import get_db
from core.models.user import User
from core.security import verify_password, hash_password, create_access_token

log = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db=Depends(get_db)):
    """
    Register a new user.
    Returns 400 if email already exists.
    """
    try:
        # Check if user already exists
        existing_user = await db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            log.warning("registration_failed_email_exists", email=user_data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        log.info("user_registered", user_id=str(new_user.id), email=user_data.email)

        return UserResponse.model_validate(new_user)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("registration_error", error=str(exc))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    """
    Login with email and password.
    Returns 401 if credentials are invalid.
    """
    try:
        # Query user by email (form_data.username is used for email in OAuth2)
        user = await db.query(User).filter(User.email == form_data.username).first()

        if not user or not verify_password(form_data.password, user.hashed_password):
            log.warning("login_failed_invalid_credentials", email=form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            log.warning("login_failed_inactive_user", user_id=str(user.id))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )

        # Create access token
        access_token = create_access_token(user_id=str(user.id))

        log.info("user_login", user_id=str(user.id), email=user.email)

        return Token(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as exc:
        log.error("login_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )
