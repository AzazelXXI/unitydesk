"""Merge heads after removing sort_order column

Revision ID: 16864cf28f64
Revises: 20250628_remove_sort_order_final, 892f759fd420
Create Date: 2025-06-28 23:20:39.031955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16864cf28f64'
down_revision: Union[str, None] = ('20250628_remove_sort_order_final', '892f759fd420')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
