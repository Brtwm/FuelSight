from __future__ import annotations

import argparse
import getpass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Role, User

REVIEWER_ROLES = ("analyst", "director")


def upsert_reviewer(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str,
    role_slug: str,
) -> bool:
    normalized_email = email.strip().lower()
    normalized_name = display_name.strip()
    if role_slug not in REVIEWER_ROLES:
        raise ValueError("reviewer_role_not_allowed")
    if not normalized_email or not normalized_name:
        raise ValueError("email_and_display_name_required")
    if len(password) < 12:
        raise ValueError("password_too_short")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("password_too_long")

    role = session.scalar(select(Role).where(Role.slug == role_slug))
    if role is None:
        raise ValueError("reviewer_role_not_seeded")

    user = session.scalar(select(User).where(User.email == normalized_email))
    created = user is None
    if user is None:
        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            display_name=normalized_name,
            role_id=role.id,
            is_active=True,
        )
        session.add(user)
    else:
        user.password_hash = hash_password(password)
        user.display_name = normalized_name
        user.role_id = role.id
        user.is_active = True
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or rotate a commission reviewer account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--role", choices=REVIEWER_ROLES, required=True)
    args = parser.parse_args()

    password = getpass.getpass("Reviewer password (12-72 UTF-8 bytes): ")
    confirmation = getpass.getpass("Confirm reviewer password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    with SessionLocal() as session:
        created = upsert_reviewer(
            session,
            email=args.email,
            password=password,
            display_name=args.display_name,
            role_slug=args.role,
        )
        session.commit()

    action = "created" if created else "updated"
    print(f"Reviewer {action}: {args.email.strip().lower()} ({args.role})")


if __name__ == "__main__":
    main()
