"""add support requests

Revision ID: 4d7b4a0d9f2a
Revises: e55ea2ccf998
Create Date: 2026-03-05 13:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d7b4a0d9f2a'
down_revision: Union[str, None] = 'e55ea2ccf998'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'support_requests',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('contact_method', sa.String(length=50), nullable=False),
        sa.Column('contact', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('new', 'in_progress', 'closed', name='support_request_status'), server_default='new', nullable=False),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_support_requests_user_id'), 'support_requests', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_support_requests_user_id'), table_name='support_requests')
    op.drop_table('support_requests')
    sa.Enum(name='support_request_status').drop(op.get_bind(), checkfirst=False)
