"""Remove role from project_members and user_type from users

Revision ID: 20250703_remove_role_and_user_type
Revises: 6bd13411e95a
Create Date: 2025-07-03 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250703_remove_role_and_user_type"
down_revision = "6bd13411e95a"
branch_labels = None
depends_on = None


def upgrade():
    # Remove 'role' column from project_members association table
    with op.batch_alter_table("project_members", schema=None) as batch_op:
        batch_op.drop_column("role")

    # Remove 'user_type' column from users table
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("user_type")


def downgrade():
    # Add 'role' column back to project_members
    with op.batch_alter_table("project_members", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "role", sa.String(length=50), nullable=False, server_default="Member"
            )
        )

    # Add 'user_type' column back to users
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "user_type", sa.String(length=50), nullable=False, server_default="user"
            )
        )
