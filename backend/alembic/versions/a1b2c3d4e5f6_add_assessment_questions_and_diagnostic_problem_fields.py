"""add diagnostic_assessment_questions table and is_diagnostic fields to problems

Revision ID: a1b2c3d4e5f6
Revises: f90a1b2c3d4e
Create Date: 2026-09-27 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f90a1b2c3d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add diagnostic-specific fields to problems table
    op.add_column('problems', sa.Column('is_diagnostic', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('problems', sa.Column('diagnostic_options', sa.JSON(), nullable=True))
    op.add_column('problems', sa.Column('diagnostic_correct_option', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_problems_is_diagnostic'), 'problems', ['is_diagnostic'], unique=False)

    # 2. Create diagnostic_assessment_questions table
    op.create_table(
        'diagnostic_assessment_questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('question_order', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['diagnostic_assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assessment_id', 'problem_id', name='uq_assessment_problem')
    )
    op.create_index(op.f('ix_diagnostic_assessment_questions_id'), 'diagnostic_assessment_questions', ['id'], unique=False)
    op.create_index(op.f('ix_diagnostic_assessment_questions_assessment_id'), 'diagnostic_assessment_questions', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_diagnostic_assessment_questions_problem_id'), 'diagnostic_assessment_questions', ['problem_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_diagnostic_assessment_questions_problem_id'), table_name='diagnostic_assessment_questions')
    op.drop_index(op.f('ix_diagnostic_assessment_questions_assessment_id'), table_name='diagnostic_assessment_questions')
    op.drop_index(op.f('ix_diagnostic_assessment_questions_id'), table_name='diagnostic_assessment_questions')
    op.drop_table('diagnostic_assessment_questions')

    op.drop_index(op.f('ix_problems_is_diagnostic'), table_name='problems')
    op.drop_column('problems', 'diagnostic_correct_option')
    op.drop_column('problems', 'diagnostic_options')
    op.drop_column('problems', 'is_diagnostic')
