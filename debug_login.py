"""
Enhanced debug script to test and fix login functionality
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_and_fix_login():
    from src.database import get_db
    from src.models.user import User, UserStatusEnum
    from src.services.auth_service import (
        authenticate_user,
        verify_password,
        get_password_hash,
    )
    from src.controllers.user_controller import login_for_access_token

    # First, let's check what UserStatusEnum values are available
    print("Available UserStatusEnum values:")
    for status in UserStatusEnum:
        print(f"  - {status.name}: {status.value}")

    # Get database session
    async for db in get_db():
        try:
            # Check if users exist
            result = await db.execute(select(User))
            users = result.scalars().all()

            print(f"\nFound {len(users)} users in database:")
            for user in users:
                print(f"  - ID: {user.id}, Name: {user.name}, Email: {user.email}")
                print(f"    User Type: {user.user_type}, Status: {user.status}")
                print(f"    Password Hash: {user.password_hash[:20]}...")

            if users:
                # Test user (first one)
                test_user = users[0]
                print(f"\n=== Testing authentication with user: {test_user.name} ===")

                # Set a known password for testing
                test_password = "password123"
                print(
                    f"Setting known password '{test_password}' for user {test_user.name}"
                )

                # Hash the new password
                new_password_hash = get_password_hash(test_password)

                # Use ONLINE status instead of ACTIVE (based on the enum values we saw)
                active_status = UserStatusEnum.ONLINE  # Change this if needed

                # Update user's password and status
                await db.execute(
                    update(User)
                    .where(User.id == test_user.id)
                    .values(
                        password_hash=new_password_hash,
                        status=active_status,  # Use the correct enum value
                    )
                )
                await db.commit()

                # Refresh the user object
                result = await db.execute(select(User).where(User.id == test_user.id))
                test_user = result.scalars().first()

                print(f"Updated password hash: {test_user.password_hash[:20]}...")
                print(f"Updated status: {test_user.status}")

                # Test password verification directly
                print(f"\n--- Testing password verification ---")
                direct_verify = verify_password(test_password, test_user.password_hash)
                print(f"Direct password verification: {direct_verify}")

                if direct_verify:
                    # Test authentication function
                    print(f"\n--- Testing authenticate_user function ---")
                    auth_result = await authenticate_user(
                        db, test_user.name, test_password
                    )
                    print(f"Authentication result: {auth_result is not None}")

                    if auth_result:
                        print(f"Authenticated user: {auth_result.name}")

                        # Test token creation
                        print(f"\n--- Testing token creation ---")
                        token = await login_for_access_token(
                            db, test_user.name, test_password
                        )

                        if token:
                            print(f"✅ SUCCESS! Token created successfully")
                            print(f"Access token: {token.access_token[:50]}...")
                            print(f"Token type: {token.token_type}")
                            print(f"Expires in: {token.expires_in} seconds")

                            # Test with email login too
                            print(f"\n--- Testing email login ---")
                            email_token = await login_for_access_token(
                                db, test_user.email, test_password
                            )
                            if email_token:
                                print(f"✅ Email login also works!")
                            else:
                                print(f"❌ Email login failed")

                        else:
                            print(f"❌ Token creation failed")
                    else:
                        print(f"❌ Authentication function failed")
                else:
                    print(f"❌ Direct password verification failed")

                # Update all users with the same password for testing
                print(f"\n=== Setting same password for all users ===")
                for user in users:
                    await db.execute(
                        update(User)
                        .where(User.id == user.id)
                        .values(
                            password_hash=new_password_hash,
                            status=active_status,  # Use the correct enum value
                        )
                    )
                    print(f"Updated password for user: {user.name}")

                await db.commit()
                print(f"\n✅ All users now have password: '{test_password}'")
                print(f"✅ All users are now {active_status}")

            else:
                print("No users found in database!")

        except Exception as e:
            logger.error(f"Debug error: {e}", exc_info=True)
        finally:
            break


if __name__ == "__main__":
    asyncio.run(debug_and_fix_login())
