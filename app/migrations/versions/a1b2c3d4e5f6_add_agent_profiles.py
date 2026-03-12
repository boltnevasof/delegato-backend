"""add agent profiles

Revision ID: a1b2c3d4e5f6
Revises: 4d7b4a0d9f2a
Create Date: 2026-03-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4d7b4a0d9f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_profiles',
        # PK
        sa.Column('id', sa.UUID(), nullable=False),
        # FK
        sa.Column('user_id', sa.UUID(), nullable=False),
        # Поля формы
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('about_self', sa.Text(), nullable=True),
        sa.Column('occupation', sa.String(length=255), nullable=True),
        sa.Column('agent_restrictions', sa.Text(), nullable=True),
        # Сгенерированные MD
        sa.Column('user_md', sa.Text(), nullable=True),
        sa.Column('agent_md', sa.Text(), nullable=True),
        sa.Column('soul_md', sa.Text(), nullable=True),
        # Служебное
        sa.Column('is_synchronized', sa.Boolean(), server_default='false', nullable=False),
        # Временные метки
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        # Constraints
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(
        'ix_agent_profiles_user_id',
        'agent_profiles',
        ['user_id'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('ix_agent_profiles_user_id', table_name='agent_profiles')
    op.drop_table('agent_profiles')
