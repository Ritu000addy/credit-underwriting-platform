from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.core.responses import success_response
from backend.app.core.security import (
    create_access_token,
    get_current_user,
)
from backend.app.database import get_db
from backend.app.models.auth_user import AuthUser
from backend.app.schemas.auth import (
    AuthUserResponse,
    TokenResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.services.auth_user_service import (
    auth_user_service,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db),
):
    user = auth_user_service.authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_USERNAME_OR_PASSWORD",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    user.last_login_at = datetime.utcnow()
    db.commit()

    access_token = create_access_token(
        user_id=user.user_id
    )

    response_data = TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

    return success_response(
        request=request,
        data=response_data,
        message="Login successful.",
    )


@router.get(
    "/me",
    response_model=ApiResponse[AuthUserResponse],
)
def get_me(
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
):
    response_data = AuthUserResponse.model_validate(
        current_user,
        from_attributes=True,
    )

    return success_response(
        request=request,
        data=response_data,
        message="Current user retrieved successfully.",
    )