from sqlalchemy.orm import Session

from backend.app.core.security import (
    DUMMY_PASSWORD_HASH,
    get_password_hash,
    verify_password,
)
from backend.app.models.auth_user import AuthUser


class AuthUserService:

    def get_by_username(
        self,
        db: Session,
        username: str,
    ) -> AuthUser | None:
        normalized_username = username.strip().lower()

        return (
            db.query(AuthUser)
            .filter(
                AuthUser.username == normalized_username
            )
            .first()
        )

    def get_by_user_id(
        self,
        db: Session,
        user_id: str,
    ) -> AuthUser | None:
        return db.get(AuthUser, user_id)

    def authenticate_user(
        self,
        db: Session,
        username: str,
        password: str,
    ) -> AuthUser | None:

        user = self.get_by_username(
            db=db,
            username=username,
        )

        if user is None:
            verify_password(
                password,
                DUMMY_PASSWORD_HASH,
            )
            return None

        if not verify_password(
            password,
            user.hashed_password,
        ):
            return None

        if not user.is_active:
            return None

        return user

    def create_user(
        self,
        db: Session,
        user_id: str,
        username: str,
        password: str,
        role: str,
        email: str | None = None,
        full_name: str | None = None,
    ) -> AuthUser:

        normalized_username = username.strip().lower()

        user = AuthUser(
            user_id=user_id,
            username=normalized_username,
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user


auth_user_service = AuthUserService()