"""merge heads after removing role and user_type

Revision ID: 412a0c6821da
Revises: 20250703_remove_role_and_user_type, 2c353cd8ab23
Create Date: 2025-07-03 12:49:34.118816

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '412a0c6821da'
down_revision: Union[str, None] = ('20250703_remove_role_and_user_type', '2c353cd8ab23')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
