from getpass import getpass
import uuid

from backend.app.database import SessionLocal
from backend.app.services.auth_user_service import auth_user_service


def main() -> None:
    username = input("Admin username: ").strip().lower()
    password = getpass("Admin password: ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        raise ValueError("PASSWORDS_DO_NOT_MATCH")

    db = SessionLocal()

    try:
        existing_user = auth_user_service.get_by_username(
            db=db,
            username=username,
        )

        if existing_user is not None:
            raise ValueError(
                "AUTH_USER_ALREADY_EXISTS"
            )

        user = auth_user_service.create_user(
            db=db,
            user_id=f"USR-{uuid.uuid4().hex[:12].upper()}",
            username=username,
            password=password,
            role="ADMIN",
        )

        print(
            f"INITIAL ADMIN CREATED: "
            f"{user.user_id} / {user.username}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()