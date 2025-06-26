#!/usr/bin/env python3
"""
Fix script for CSA Platform Activity Service.
This script will fix the issues in the ActivityService to make activities work properly.
"""

import os
import sys


def fix_activity_service():
    """Fix the ActivityService implementation"""

    print("=" * 60)
    print("FIXING CSA PLATFORM ACTIVITY SERVICE")
    print("=" * 60)

    # Fix 1: Update ActivityService to use extra_data instead of metadata
    activity_service_path = "src/services/activity_service.py"

    if not os.path.exists(activity_service_path):
        print(f"❌ ERROR: {activity_service_path} not found!")
        return False

    print(f"✅ Reading {activity_service_path}...")

    with open(activity_service_path, "r") as f:
        content = f.read()

    # Replace metadata with extra_data in the log_activity method
    if "metadata: dict = None" in content:
        content = content.replace("metadata: dict = None", "extra_data: dict = None")
        print("✅ Fixed parameter name: metadata -> extra_data")

    if "metadata=metadata" in content:
        content = content.replace("metadata=metadata", "extra_data=extra_data")
        print("✅ Fixed parameter usage: metadata -> extra_data")

    # Fix the ProjectActivity creation to use extra_data
    if "metadata=json.dumps(metadata)" in content:
        content = content.replace(
            "metadata=json.dumps(metadata)", "extra_data=json.dumps(extra_data)"
        )
        print("✅ Fixed ProjectActivity creation parameter")

    # Write the fixed content back
    with open(activity_service_path, "w") as f:
        f.write(content)

    print(f"✅ Updated {activity_service_path}")

    # Fix 2: Update project_routes.py to use extra_data instead of metadata
    project_routes_path = "src/views/project/project_routes.py"

    if not os.path.exists(project_routes_path):
        print(f"❌ ERROR: {project_routes_path} not found!")
        return False

    print(f"✅ Reading {project_routes_path}...")

    with open(project_routes_path, "r") as f:
        routes_content = f.read()

    # Replace metadata with extra_data in activity logging calls
    if "metadata={" in routes_content:
        routes_content = routes_content.replace("metadata={", "extra_data={")
        print("✅ Fixed activity logging calls: metadata -> extra_data")

    # Write the fixed content back
    with open(project_routes_path, "w") as f:
        f.write(routes_content)

    print(f"✅ Updated {project_routes_path}")

    print(f"\n" + "=" * 60)
    print("ACTIVITY SERVICE FIXES COMPLETED!")
    print("=" * 60)
    print("Changes made:")
    print(
        "1. Fixed parameter name in ActivityService.log_activity: metadata -> extra_data"
    )
    print("2. Fixed ProjectActivity creation to use extra_data column")
    print("3. Fixed activity logging calls in project routes")
    print()
    print("Next steps:")
    print("1. Run the test_activities.py script to verify fixes")
    print("2. Restart your web application")
    print("3. Test creating tasks and adding members to generate activities")

    return True


if __name__ == "__main__":
    success = fix_activity_service()
    if success:
        print("\n✅ All fixes applied successfully!")
    else:
        print("\n❌ Some fixes failed. Check the errors above.")
