"""create recommendations table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-28 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'recommendations',
        sa.Column('recommendation_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('recommendation_id'),
        sa.UniqueConstraint('user_id', 'problem_id', name='uq_user_problem_recommendation')
    )
    op.create_index(op.f('ix_recommendations_recommendation_id'), 'recommendations', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_recommendations_user_id'), 'recommendations', ['user_id'], unique=False)
    op.create_index(op.f('ix_recommendations_problem_id'), 'recommendations', ['problem_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_recommendations_problem_id'), table_name='recommendations')
    op.drop_index(op.f('ix_recommendations_user_id'), table_name='recommendations')
    op.drop_index(op.f('ix_recommendations_recommendation_id'), table_name='recommendations')
    op.drop_table('recommendations')
