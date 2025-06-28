"""
Revision ID: 20250628_remove_sort_order_final
Revises: 58a38c0df9ac
Create Date: 2025-06-28

Remove 'sort_order' column from custom_project_statuses table (final cleanup).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250628_remove_sort_order_final"
down_revision = "58a38c0df9ac"
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
