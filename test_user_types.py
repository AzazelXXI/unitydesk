#!/usr/bin/env python3
"""
Test script for the flexible user type system
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))

from src.database import get_db
from src.services.user_type_service import UserTypeService
from src.models.user import (
    get_available_user_types,
    is_valid_user_type,
    get_user_type_display_name,
)


async def test_user_type_system():
    """Test the user type system"""
    print("🔧 Testing User Type System")
    print("=" * 50)

    # Initialize database
    await init_db()

    # Test default functionality (without database)
    print("\n📋 Default User Types (without database):")
    default_types = get_available_user_types()
    for user_type in default_types:
        display_name = get_user_type_display_name(user_type)
        is_valid = is_valid_user_type(user_type)
        print(f"  • {user_type} → {display_name} (Valid: {is_valid})")

    # Test with database
    print("\n🗄️ Testing with Database:")
    async for db in get_db_async():
        try:
            # Get all user types (default + custom)
            all_types = await UserTypeService.get_all_user_types(db)
            print(f"\nTotal user types available: {len(all_types)}")

            for user_type in all_types:
                type_indicator = (
                    "🔧 Custom" if user_type.get("is_custom", False) else "📦 Default"
                )
                print(
                    f"  {type_indicator}: {user_type['type_name']} → {user_type['display_name']}"
                )
                if user_type.get("description"):
                    print(f"    Description: {user_type['description']}")

            # Test creating a custom user type
            print("\n➕ Creating custom user type...")
            try:
                custom_type = await UserTypeService.create_custom_user_type(
                    db=db,
                    type_name="data_scientist",
                    display_name="Data Scientist",
                    description="Analyzes data and creates machine learning models",
                )
                print(f"✅ Created custom user type: {custom_type.type_name}")
            except ValueError as e:
                print(f"ℹ️ Custom type already exists: {e}")

            # Test another custom user type
            try:
                custom_type2 = await UserTypeService.create_custom_user_type(
                    db=db,
                    type_name="devops_engineer",
                    display_name="DevOps Engineer",
                    description="Manages infrastructure and deployment pipelines",
                )
                print(f"✅ Created custom user type: {custom_type2.type_name}")
            except ValueError as e:
                print(f"ℹ️ Custom type already exists: {e}")

            # Get updated list
            print("\n📊 Updated user types list:")
            updated_types = await UserTypeService.get_all_user_types(db)
            print(f"Total user types now: {len(updated_types)}")

            for user_type in updated_types:
                type_indicator = (
                    "🔧 Custom" if user_type.get("is_custom", False) else "📦 Default"
                )
                print(
                    f"  {type_indicator}: {user_type['type_name']} → {user_type['display_name']}"
                )

            # Test validation
            print("\n🔍 Testing validation:")
            test_types = [
                "developer",
                "data_scientist",
                "invalid_type",
                "project_manager",
            ]
            for test_type in test_types:
                is_valid = await UserTypeService.is_valid_user_type(db, test_type)
                display_name = await UserTypeService.get_user_type_display_name(
                    db, test_type
                )
                status = "✅ Valid" if is_valid else "❌ Invalid"
                print(f"  {test_type} → {display_name} ({status})")

            print("\n✅ User type system test completed successfully!")

        except Exception as e:
            print(f"❌ Error during database test: {str(e)}")
            import traceback

            traceback.print_exc()
        finally:
            await db.close()


if __name__ == "__main__":
    print("🚀 Starting User Type System Test")
    asyncio.run(test_user_type_system())
