"""merge comment_attachments branch

Revision ID: 974f2587cd97
Revises: f8287dd7325a, 20250708_add_comment_attachments
Create Date: 2025-07-09 20:38:28.281648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '974f2587cd97'
down_revision: Union[str, None] = ('f8287dd7325a', '20250708_add_comment_attachments')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
