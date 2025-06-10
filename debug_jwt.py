#!/usr/bin/env python3
"""
Debug script to test JWT token creation and verification
"""
import asyncio
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.services.auth_service import create_access_token, verify_token
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_jwt():
    """Test JWT token creation and verification"""
    # Test data similar to what the login creates (with enum value, not name)
    test_data = {
        "sub": "John PM",  # This is user.name from database
        "id": 1,  # user.id
        "role": "project_manager",  # user.user_type.value (not user.user_type)
    }

    logger.info(f"Creating token with data: {test_data}")

    # Create token
    token = await create_access_token(test_data)
    logger.info(f"Created token: {token[:50]}...")

    # Verify token
    token_data = await verify_token(token)
    logger.info(f"Verified token data: {token_data}")

    if token_data:
        logger.info("✅ JWT creation and verification working correctly")
    else:
        logger.error("❌ JWT verification failed")


if __name__ == "__main__":
    asyncio.run(test_jwt())
