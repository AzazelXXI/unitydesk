"""
Revision ID: 20250628_remove_sort_order
Revises:
Create Date: 2025-06-28

Alembic migration to remove the 'sort_order' column from custom_project_statuses table.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250628_remove_sort_order"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("custom_project_statuses") as batch_op:
        batch_op.drop_column("sort_order")


def downgrade():
    with op.batch_alter_table("custom_project_statuses") as batch_op:
        batch_op.add_column(
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0")
        )
