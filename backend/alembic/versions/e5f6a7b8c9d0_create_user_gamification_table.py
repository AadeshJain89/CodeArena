"""create user_gamification table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-28 12:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_gamification',
        sa.Column('gamification_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('xp', sa.Integer(), server_default='0', nullable=False),
        sa.Column('level', sa.Integer(), server_default='1', nullable=False),
        sa.Column('problems_solved', sa.Integer(), server_default='0', nullable=False),
        sa.Column('successful_submissions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('current_streak', sa.Integer(), server_default='0', nullable=False),
        sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_activity_date', sa.Date(), nullable=True),
        sa.Column('badges', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('gamification_id'),
        sa.UniqueConstraint('user_id', name='uq_user_gamification')
    )
    op.create_index(op.f('ix_user_gamification_gamification_id'), 'user_gamification', ['gamification_id'], unique=False)
    op.create_index(op.f('ix_user_gamification_user_id'), 'user_gamification', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_gamification_user_id'), table_name='user_gamification')
    op.drop_index(op.f('ix_user_gamification_gamification_id'), table_name='user_gamification')
    op.drop_table('user_gamification')
