"""Merge heads for ON DELETE CASCADE and sort order removal

Revision ID: 2c353cd8ab23
Revises: 20250628_remove_sort_order, add_on_delete_cascade_notifications_task_id
Create Date: 2025-07-02 19:33:15.591290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c353cd8ab23'
down_revision: Union[str, None] = ('20250628_remove_sort_order', 'add_on_delete_cascade_notifications_task_id')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
