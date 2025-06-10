"""
Quick setup script to create test users for Project/Task module testing
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.models.user import (
    User,
    ProjectManager,
    TeamLeader,
    Developer,
    Designer,
    Tester,
)
from src.database import DATABASE_URL
from src.services.auth_service import get_password_hash


async def create_test_users():
    """Create test users for development"""

    # Use your database connection
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            print("🔧 Creating test users for Project/Task module...")

            # Common password for all test users (for easy testing)
            test_password = "password123"
            hashed_password = get_password_hash(test_password)

            # Create test users with proper password hashes
            test_users_data = [
                {
                    "class": ProjectManager,
                    "name": "John Manager",
                    "email": "john.pm@company.com",
                },
                {
                    "class": TeamLeader,
                    "name": "Sarah Leader",
                    "email": "sarah.tl@company.com",
                },
                {
                    "class": Developer,
                    "name": "Alice Developer",
                    "email": "alice.dev@company.com",
                },
                {
                    "class": Designer,
                    "name": "Bob Designer",
                    "email": "bob.designer@company.com",
                },
                {
                    "class": Tester,
                    "name": "Charlie Tester",
                    "email": "charlie.tester@company.com",
                },
            ]  # Check if users already exist and create new ones
            existing_emails = []
            created_users = []

            for user_data in test_users_data:
                # Check if user already exists
                result = await db.execute(
                    select(User).where(User.email == user_data["email"])
                )
                existing_user = result.scalars().first()

                if existing_user:
                    existing_emails.append(user_data["email"])
                    print(f"⚠️  User {user_data['email']} already exists, skipping...")
                else:
                    user = user_data["class"](
                        name=user_data["name"],  # User model uses 'name' not 'username'
                        email=user_data["email"],
                        password_hash=hashed_password,  # User model uses 'password_hash'
                        phone=None,
                        avatar=None,
                    )
                    db.add(user)
                    created_users.append(user_data["email"])
                    print(
                        f"✅ Created user: {user_data['name']} ({user_data['email']})"
                    )

            # Commit the changes
            await db.commit()

            # Display all users
            result = await db.execute(
                select(User.id, User.name, User.user_type, User.email)
            )
            users = result.all()

            print("\n✅ Test users ready:")
            for user_id, name, user_type, email in users:
                print(f"   - {name} (ID: {user_id}, Type: {user_type}, Email: {email})")

            print(f"\n🔑 All test users use password: '{test_password}'")
            print("\n📋 Authentication Examples:")
            print("POST /api/users/auth/login")
            print("Content-Type: application/x-www-form-urlencoded")
            print("username=john.pm@company.com&password=password123")
            print("\nOR using JSON:")
            print('{"username": "john.pm@company.com", "password": "password123"}')
            print("\n🔗 Login with any of these emails and password 'password123'")

            print(
                "\n🚀 You can now test the Project/Task APIs with real authentication!"
            )

        except Exception as e:
            print(f"❌ Error creating test users: {str(e)}")
            import traceback

            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(create_test_users())
