
import os
import sys
from getpass import getpass
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()

from backend.app.database import DATABASE_URL, SessionLocal
from backend.app.models.auth_user import AuthUser
from backend.app.services.auth_user_service import auth_user_service


def main() -> int:
    # Restrict this bootstrap to a local development database.
    environment = os.getenv("APP_ENV", "development").lower()
    database_host = make_url(DATABASE_URL).host

    if environment != "development":
        print("Refused: APP_ENV must be development.")
        return 1

    if database_host not in {"localhost", "127.0.0.1", "::1"}:
        print("Refused: bootstrap is restricted to a local database.")
        return 1

    username = input("Initial admin username: ").strip().lower()
    if not username:
        print("Username is required.")
        return 1

    full_name = input("Admin display name (optional): ").strip() or None

    password = getpass("Admin password (minimum 14 characters): ")
    confirmation = getpass("Confirm admin password: ")

    if password != confirmation:
        print("Passwords do not match.")
        return 1

    if len(password) < 14:
        print("Password must contain at least 14 characters.")
        return 1

    db = SessionLocal()

    try:
        # This must remain a first-user-only bootstrap.
        if db.query(AuthUser).count() != 0:
            print("Refused: auth_users already contains user records.")
            return 1

        user = auth_user_service.create_user(
            db=db,
            user_id=f"USR-{uuid4().hex[:12].upper()}",
            username=username,
            password=password,
            role="ADMIN",
            email=None,
            full_name=full_name,
        )

        print("Initial admin created successfully.")
        print(f"User ID: {user.user_id}")
        print(f"Username: {user.username}")
        print(f"Role: {user.role}")
        print("Password was not displayed.")

        return 0

    except Exception as exc:
        db.rollback()
        print(f"Admin creation failed ({type(exc).__name__}).")
        print("No password was displayed. Check the database error.")
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
