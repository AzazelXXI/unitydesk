"""
Add comment_attachments association table
"""

# Alembic revision identifiers, used by Alembic.
revision = "20250708_add_comment_attachments"
down_revision = "20250703_drop_department_tables"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "comment_attachments",
        sa.Column(
            "comment_id", sa.Integer(), sa.ForeignKey("comments.id"), primary_key=True
        ),
        sa.Column(
            "attachment_id",
            sa.Integer(),
            sa.ForeignKey("attachments.id"),
            primary_key=True,
        ),
    )


def downgrade():
    op.drop_table("comment_attachments")
