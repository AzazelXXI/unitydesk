"""Initial migration

Revision ID: 6bd13411e95a
Revises: e0dcc7a40331
Create Date: 2025-06-23 19:47:39.032268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bd13411e95a'
down_revision: Union[str, None] = 'e0dcc7a40331'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
