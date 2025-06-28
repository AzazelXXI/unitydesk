"""
User Type Service - Manages both default and custom user types
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Dict, Optional
import logging

from src.models.custom_user_type import CustomUserType
from src.models.user import DEFAULT_USER_TYPES, UserTypeEnum

logger = logging.getLogger(__name__)


class UserTypeService:
    """Service for managing user types (default + custom)"""

    @staticmethod
    async def get_all_user_types(db: AsyncSession) -> List[Dict[str, str]]:
        """
        Get all available user types (default + custom)
        Returns list of dicts with type_name and display_name
        """
        try:
            user_types = []
            
            # Add default user types
            for user_type in DEFAULT_USER_TYPES:
                display_name = user_type.replace('_', ' ').title()
                user_types.append({
                    'type_name': user_type,
                    'display_name': display_name,
                    'is_custom': False,
                    'description': f'Default {display_name} role'
                })
            
            # Get custom user types from database
            query = select(CustomUserType).where(CustomUserType.is_active == True)
            result = await db.execute(query)
            custom_types = result.scalars().all()
            
            for custom_type in custom_types:
                user_types.append({
                    'type_name': custom_type.type_name,
                    'display_name': custom_type.display_name,
                    'is_custom': True,
                    'description': custom_type.description or f'Custom {custom_type.display_name} role'
                })
            
            return user_types
            
        except Exception as e:
            logger.error(f"Error getting user types: {str(e)}")
            # Fallback to default types only
            return [
                {
                    'type_name': user_type,
                    'display_name': user_type.replace('_', ' ').title(),
                    'is_custom': False,
                    'description': f'Default {user_type.replace("_", " ").title()} role'
                }
                for user_type in DEFAULT_USER_TYPES
            ]

    @staticmethod
    async def get_user_type_names(db: AsyncSession) -> List[str]:
        """Get list of all available user type names"""
        try:
            user_types = await UserTypeService.get_all_user_types(db)
            return [ut['type_name'] for ut in user_types]
        except Exception as e:
            logger.error(f"Error getting user type names: {str(e)}")
            return DEFAULT_USER_TYPES.copy()

    @staticmethod
    async def is_valid_user_type(db: AsyncSession, user_type: str) -> bool:
        """Check if a user type is valid (exists in default or custom types)"""
        try:
            available_types = await UserTypeService.get_user_type_names(db)
            return user_type in available_types
        except Exception as e:
            logger.error(f"Error validating user type: {str(e)}")
            return user_type in DEFAULT_USER_TYPES

    @staticmethod
    async def create_custom_user_type(
        db: AsyncSession,
        type_name: str,
        display_name: str,
        description: str = None
    ) -> CustomUserType:
        """Create a new custom user type"""
        try:
            # Check if type already exists
            existing_query = select(CustomUserType).where(
                CustomUserType.type_name == type_name.lower().replace(' ', '_')
            )
            existing = await db.execute(existing_query)
            if existing.scalar_one_or_none():
                raise ValueError(f"User type '{type_name}' already exists")
            
            # Check if it conflicts with default types
            if type_name.lower().replace(' ', '_') in DEFAULT_USER_TYPES:
                raise ValueError(f"User type '{type_name}' conflicts with default types")
            
            custom_type = CustomUserType(
                type_name=type_name,
                display_name=display_name,
                description=description
            )
            
            db.add(custom_type)
            await db.commit()
            await db.refresh(custom_type)
            
            logger.info(f"Created custom user type: {custom_type.type_name}")
            return custom_type
            
        except Exception as e:
            logger.error(f"Error creating custom user type: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def update_custom_user_type(
        db: AsyncSession,
        type_id: int,
        display_name: str = None,
        description: str = None,
        is_active: bool = None
    ) -> CustomUserType:
        """Update an existing custom user type"""
        try:
            query = select(CustomUserType).where(CustomUserType.id == type_id)
            result = await db.execute(query)
            custom_type = result.scalar_one_or_none()
            
            if not custom_type:
                raise ValueError(f"Custom user type with ID {type_id} not found")
            
            if display_name is not None:
                custom_type.display_name = display_name
            if description is not None:
                custom_type.description = description
            if is_active is not None:
                custom_type.is_active = is_active
            
            await db.commit()
            await db.refresh(custom_type)
            
            logger.info(f"Updated custom user type: {custom_type.type_name}")
            return custom_type
            
        except Exception as e:
            logger.error(f"Error updating custom user type: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_custom_user_type(db: AsyncSession, type_id: int) -> bool:
        """Delete (deactivate) a custom user type"""
        try:
            query = select(CustomUserType).where(CustomUserType.id == type_id)
            result = await db.execute(query)
            custom_type = result.scalar_one_or_none()
            
            if not custom_type:
                raise ValueError(f"Custom user type with ID {type_id} not found")
            
            # Check if any users are using this type
            users_with_type_query = text(
                "SELECT COUNT(*) FROM users WHERE user_type = :user_type"
            )
            result = await db.execute(users_with_type_query, {"user_type": custom_type.type_name})
            user_count = result.scalar()
            
            if user_count > 0:
                # Deactivate instead of delete if users are using it
                custom_type.is_active = False
                await db.commit()
                logger.info(f"Deactivated custom user type: {custom_type.type_name} (used by {user_count} users)")
                return False
            else:
                # Safe to delete
                await db.delete(custom_type)
                await db.commit()
                logger.info(f"Deleted custom user type: {custom_type.type_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting custom user type: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def get_user_type_display_name(db: AsyncSession, type_name: str) -> str:
        """Get display name for a user type"""
        try:
            # Check custom types first
            query = select(CustomUserType).where(
                CustomUserType.type_name == type_name,
                CustomUserType.is_active == True
            )
            result = await db.execute(query)
            custom_type = result.scalar_one_or_none()
            
            if custom_type:
                return custom_type.display_name
            
            # Check default types
            if type_name in DEFAULT_USER_TYPES:
                return type_name.replace('_', ' ').title()
            
            # Fallback
            return type_name.replace('_', ' ').title()
            
        except Exception as e:
            logger.error(f"Error getting display name for user type: {str(e)}")
            return type_name.replace('_', ' ').title()
