from __future__ import annotations

import argparse
import os
import secrets
import sys
from getpass import getpass

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.schemas import UserCreate
from app.services.auth import AuthService


def _read_secret(prompt: str) -> str:
    value = getpass(prompt)
    if not value:
        raise ValueError(f"{prompt.strip(': ')} is required.")
    return value


def create_admin_user(*, email: str, password: str, bootstrap_token: str) -> dict:
    expected_token = os.getenv("COLA_ZERO_ADMIN_BOOTSTRAP_TOKEN")
    if not expected_token:
        raise RuntimeError(
            "COLA_ZERO_ADMIN_BOOTSTRAP_TOKEN is not configured. "
            "Refusing to create an admin account."
        )
    if not secrets.compare_digest(bootstrap_token, expected_token):
        raise PermissionError("Invalid bootstrap token.")

    db = SessionLocal()
    try:
        service = AuthService(db)
        user = service.register_user(
            UserCreate(
                email=email,
                password=password,
                role=UserRole.ADMIN,
            )
        )
        return user
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a protected admin user for COLA-ZERO.",
    )
    parser.add_argument("--email", required=True, help="Admin email address.")
    parser.add_argument(
        "--password",
        help="Admin password. If omitted, the script prompts securely.",
    )
    parser.add_argument(
        "--bootstrap-token",
        help="Bootstrap token. If omitted, the script prompts securely.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    password = args.password or _read_secret("Admin password: ")
    bootstrap_token = args.bootstrap_token or _read_secret("Bootstrap token: ")

    try:
        user = create_admin_user(
            email=args.email,
            password=password,
            bootstrap_token=bootstrap_token,
        )
    except (RuntimeError, PermissionError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Admin created: {user['email']} ({user['id']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
