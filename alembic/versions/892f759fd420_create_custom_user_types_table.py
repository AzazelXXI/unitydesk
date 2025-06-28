"""Create custom user types table

Revision ID: 892f759fd420
Revises: add_custom_user_types
Create Date: 2025-06-28 10:41:46.935588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '892f759fd420'
down_revision: Union[str, None] = 'add_custom_user_types'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
