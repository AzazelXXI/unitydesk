"""merge department table drops and other heads

Revision ID: f8287dd7325a
Revises: 20250703_drop_department_tables, 412a0c6821da, ab12cdef3456
Create Date: 2025-07-03 22:03:21.034640

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8287dd7325a"
down_revision: Union[str, None] = (
    "20250703_drop_department_tables",
    "412a0c6821da",
    "ab12cdef3456",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This is a merge migration; no schema changes needed.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This is a merge migration; no schema changes needed.
    pass
