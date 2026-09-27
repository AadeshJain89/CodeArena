import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole


async def seed_admin():
    async with AsyncSessionLocal() as session:
        # Check if admin already exists
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()

        if admin:
            print("Admin user 'admin' already exists.")
            return

        admin_user = User(
            username="admin",
            email="admin@codearena.com",
            password_hash=hash_password("Admin@123456"),
            role=UserRole.ADMIN,
            is_active=True,
        )

        session.add(admin_user)
        await session.commit()
        print("Successfully created ADMIN user: username='admin', password='Admin@123456'")


if __name__ == "__main__":
    asyncio.run(seed_admin())
