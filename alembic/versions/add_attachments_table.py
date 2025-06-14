"""Add attachments table

Revision ID: add_attachments_table
Create Date: 2025-06-14

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = "add_attachments_table"
down_revision = None  # Update this if you have other migrations
branch_labels = None
depends_on = None


def upgrade():
    """Create attachments table"""

    # Create attachments table
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create foreign key constraints
    op.create_foreign_key(
        "fk_attachments_user_id",
        "attachments",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_attachments_task_id",
        "attachments",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create indexes for better performance
    op.create_index("idx_attachments_task_id", "attachments", ["task_id"])
    op.create_index("idx_attachments_user_id", "attachments", ["user_id"])

    print("✅ Attachments table created successfully")


def downgrade():
    """Drop attachments table"""
    op.drop_index("idx_attachments_user_id")
    op.drop_index("idx_attachments_task_id")
    op.drop_constraint("fk_attachments_task_id", "attachments", type_="foreignkey")
    op.drop_constraint("fk_attachments_user_id", "attachments", type_="foreignkey")
    op.drop_table("attachments")
    print("❌ Attachments table dropped")
