"""
Add comment_attachments association table
"""

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
