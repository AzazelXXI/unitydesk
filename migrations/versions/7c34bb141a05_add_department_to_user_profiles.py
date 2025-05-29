"""add_department_to_user_profiles

Revision ID: 7c34bb141a05
Revises: 13d6a90e1318
Create Date: 2025-05-28 23:12:02.317276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c34bb141a05'
down_revision: Union[str, None] = '13d6a90e1318'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
