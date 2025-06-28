"""rename_metadata_to_activity_data_in_project_activities

Revision ID: 58a38c0df9ac
Revises: 109990564e22
Create Date: 2025-06-27 00:11:35.142048

This migration is now a no-op because the 'metadata' column does not exist in the database.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "58a38c0df9ac"
down_revision: Union[str, None] = "109990564e22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op: 'metadata' column does not exist, nothing to rename
    pass


def downgrade() -> None:
    # No-op: nothing to revert
    pass
