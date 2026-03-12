"""split agent_profiles: move MD fields to agent_documents

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Создаём таблицу agent_documents
    op.create_table(
        'agent_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('user_md', sa.Text(), nullable=True),
        sa.Column('agent_md', sa.Text(), nullable=True),
        sa.Column('soul_md', sa.Text(), nullable=True),
        sa.Column('is_synchronized', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_agent_documents_user_id', 'agent_documents', ['user_id'], unique=True)

    # 2. Переносим существующие MD-данные из agent_profiles в agent_documents
    op.execute("""
        INSERT INTO agent_documents (id, user_id, user_md, agent_md, soul_md, is_synchronized, created_at, updated_at)
        SELECT gen_random_uuid(), user_id, user_md, agent_md, soul_md, is_synchronized, created_at, updated_at
        FROM agent_profiles
        WHERE user_md IS NOT NULL OR agent_md IS NOT NULL OR soul_md IS NOT NULL
    """)

    # 3. Удаляем MD-колонки и is_synchronized из agent_profiles
    op.drop_column('agent_profiles', 'user_md')
    op.drop_column('agent_profiles', 'agent_md')
    op.drop_column('agent_profiles', 'soul_md')
    op.drop_column('agent_profiles', 'is_synchronized')


def downgrade() -> None:
    # Возвращаем колонки в agent_profiles
    op.add_column('agent_profiles', sa.Column('user_md', sa.Text(), nullable=True))
    op.add_column('agent_profiles', sa.Column('agent_md', sa.Text(), nullable=True))
    op.add_column('agent_profiles', sa.Column('soul_md', sa.Text(), nullable=True))
    op.add_column('agent_profiles', sa.Column('is_synchronized', sa.Boolean(), server_default='false', nullable=False))

    # Переносим данные обратно
    op.execute("""
        UPDATE agent_profiles ap
        SET user_md = d.user_md, agent_md = d.agent_md, soul_md = d.soul_md, is_synchronized = d.is_synchronized
        FROM agent_documents d
        WHERE ap.user_id = d.user_id
    """)

    op.drop_index('ix_agent_documents_user_id', table_name='agent_documents')
    op.drop_table('agent_documents')
