"""create skill_profiles table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-27 22:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'skill_profiles',
        sa.Column('skill_profile_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('skill_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('skill_level', sa.String(length=50), server_default='BEGINNER', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('problems_solved', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_points', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('skill_profile_id'),
        sa.UniqueConstraint('user_id', 'topic_id', name='uq_user_topic_skill')
    )
    op.create_index(op.f('ix_skill_profiles_skill_profile_id'), 'skill_profiles', ['skill_profile_id'], unique=False)
    op.create_index(op.f('ix_skill_profiles_user_id'), 'skill_profiles', ['user_id'], unique=False)
    op.create_index(op.f('ix_skill_profiles_topic_id'), 'skill_profiles', ['topic_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_skill_profiles_topic_id'), table_name='skill_profiles')
    op.drop_index(op.f('ix_skill_profiles_user_id'), table_name='skill_profiles')
    op.drop_index(op.f('ix_skill_profiles_skill_profile_id'), table_name='skill_profiles')
    op.drop_table('skill_profiles')
