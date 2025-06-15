"""Add Under Review status to task_status_enum

Revision ID: add_under_review_status
Revises:
Create Date: 2025-06-15 09:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_under_review_status"
down_revision = "4377e4c06209"  # Replace with your latest revision
branch_labels = None
depends_on = None


def upgrade():
    """Add 'Under Review' to the task_status_enum"""

    # Add the new enum value to task_status_enum
    op.execute("ALTER TYPE task_status_enum ADD VALUE 'Under Review'")


def downgrade():
    """Remove 'Under Review' from task_status_enum"""

    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type and updating all references
    # For simplicity, we'll leave this as a placeholder
    pass
