"""Create custom_user_types table

Revision ID: add_custom_user_types
Revises:
Create Date: 2025-06-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_custom_user_types"
down_revision = "58a38c0df9ac"
depends_on = None


def upgrade():
    # Create custom_user_types table
    op.create_table(
        "custom_user_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type_name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type_name"),
    )

    # Create index for active user types
    op.create_index(
        "ix_custom_user_types_is_active",
        "custom_user_types",
        ["is_active"],
        unique=False,
    )


def downgrade():
    # Drop the table and indexes
    op.drop_index("ix_custom_user_types_is_active", table_name="custom_user_types")
    op.drop_table("custom_user_types")
