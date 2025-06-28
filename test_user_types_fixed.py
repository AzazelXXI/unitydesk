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

    # Test default functionality (without database)
    print("\n📋 Default User Types (without database):")
    default_types = get_available_user_types()
    for user_type in default_types:
        display_name = get_user_type_display_name(user_type)
        is_valid = is_valid_user_type(user_type)
        print(f"  • {user_type} → {display_name} (Valid: {is_valid})")

    # Test with database
    print("\n🗄️ Testing with Database:")
    async for db in get_db():
        try:
            # Initialize default types first
            print("\n🔄 Initializing default user types in database...")
            await UserTypeService.initialize_default_types(db)
            print("✅ Default types initialized")

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
                    db,
                    type_name="qa_engineer",
                    display_name="QA Engineer",
                    description="Quality Assurance Engineer responsible for testing and validation",
                )
                print(f"✅ Created: {custom_type.display_name}")

                # Test validation of the new custom type
                is_valid = await UserTypeService.is_valid_user_type(db, "qa_engineer")
                print(
                    f"   Validation check: {'✅ Valid' if is_valid else '❌ Invalid'}"
                )

            except Exception as e:
                print(f"   Note: {str(e)} (might already exist)")

            # Test some validations
            print("\n🔍 Testing user type validations:")
            test_types = ["developer", "qa_engineer", "invalid_type", "project_manager"]
            for user_type in test_types:
                is_valid = await UserTypeService.is_valid_user_type(db, user_type)
                status = "✅" if is_valid else "❌"
                print(f"  {status} {user_type}")

                # Get details
                details = await UserTypeService.get_user_type_details(db, user_type)
                if details:
                    print(f"     Display: {details['display_name']}")
                    if details.get("description"):
                        print(f"     Description: {details['description']}")

            # Test getting display names
            print("\n📝 Testing display name service:")
            for user_type in ["developer", "qa_engineer", "project_manager"]:
                display_name = await UserTypeService.get_user_type_display_name(
                    db, user_type
                )
                print(f"  {user_type} → {display_name}")

            print("\n🎉 All tests completed successfully!")

        except Exception as e:
            print(f"\n❌ Error during database testing: {str(e)}")
            import traceback

            traceback.print_exc()

        break  # Exit after first session


if __name__ == "__main__":
    print("Starting User Type System Tests...")
    asyncio.run(test_user_type_system())
