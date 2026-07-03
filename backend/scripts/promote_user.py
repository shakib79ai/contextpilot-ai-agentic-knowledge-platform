"""One-off CLI to promote an existing user to reviewer or admin.

There's no bootstrap "first admin" flow via the API on purpose — role
escalation is a privileged operation and should go through direct DB/ops
access, not an HTTP endpoint. Register the user normally via
POST /api/v1/auth/register first, then run this.

Usage (from backend/, with the venv/deps active, or via docker-compose):
    python scripts/promote_user.py --email you@example.com --role reviewer
    docker-compose exec backend python scripts/promote_user.py --email you@example.com --role admin
"""
import argparse
import sys

from app.database import SessionLocal
from app.models.enums import UserRole
from app.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a user to reviewer or admin.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=[r.value for r in UserRole])
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email).first()
        if user is None:
            print(f"No user found with email {args.email}", file=sys.stderr)
            raise SystemExit(1)

        user.role = UserRole(args.role)
        db.commit()
        print(f"{args.email} is now '{user.role.value}'")
    finally:
        db.close()


if __name__ == "__main__":
    main()
