"""
Drop department-related tables: departments, positions, department_memberships
"""

# Alembic revision identifiers, used by Alembic.
revision = "20250703_drop_department_tables"
down_revision = "20250628_remove_sort_order_final"
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table("department_memberships")
    op.drop_table("positions")
    op.drop_table("departments")


def downgrade():
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(length=100), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "code", sa.String(length=20), unique=True, nullable=False, index=True
        ),
        sa.Column(
            "parent_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True
        ),
        sa.Column("manager_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(length=100), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id"),
            nullable=False,
        ),
        sa.Column("level", sa.Integer(), default=1, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "department_memberships",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id"),
            nullable=False,
        ),
        sa.Column(
            "position_id", sa.Integer(), sa.ForeignKey("positions.id"), nullable=False
        ),
        sa.Column(
            "start_date",
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.now(),
        ),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_primary", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
