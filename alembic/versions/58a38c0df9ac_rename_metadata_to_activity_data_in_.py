"""rename_metadata_to_activity_data_in_project_activities

Revision ID: 58a38c0df9ac
Revises: 109990564e22
Create Date: 2025-06-27 00:11:35.142048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58a38c0df9ac'
down_revision: Union[str, None] = '109990564e22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename metadata column to activity_data in project_activities table
    op.alter_column('project_activities', 'metadata', new_column_name='activity_data')


def downgrade() -> None:
    """Downgrade schema."""
    # Revert the column name change
    op.alter_column('project_activities', 'activity_data', new_column_name='metadata')
