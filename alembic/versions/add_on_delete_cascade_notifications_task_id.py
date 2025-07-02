"""
Add ON DELETE CASCADE to notifications.task_id foreign key

Revision ID: add_on_delete_cascade_notifications_task_id
Revises: 16864cf28f64
Create Date: 2025-07-02 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_on_delete_cascade_notifications_task_id'
down_revision = '16864cf28f64'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop the old foreign key constraint
    op.drop_constraint('notifications_task_id_fkey', 'notifications', type_='foreignkey')
    # Add new foreign key with ON DELETE CASCADE
    op.create_foreign_key(
        'notifications_task_id_fkey',
        'notifications', 'tasks',
        ['task_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    # Drop the ON DELETE CASCADE constraint
    op.drop_constraint('notifications_task_id_fkey', 'notifications', type_='foreignkey')
    # Recreate the original foreign key without ON DELETE CASCADE
    op.create_foreign_key(
        'notifications_task_id_fkey',
        'notifications', 'tasks',
        ['task_id'], ['id']
    )
