"""create diagnostic_assessments and diagnostic_responses tables and add MCQ fields to problems

Revision ID: f90a1b2c3d4e
Revises: e89f1a2b3c4d
Create Date: 2026-09-27 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f90a1b2c3d4e'
down_revision: Union[str, None] = 'e89f1a2b3c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add MCQ metadata fields to problems table
    op.add_column('problems', sa.Column('question_type', sa.String(length=50), nullable=True, server_default='CODING'))
    op.add_column('problems', sa.Column('options', sa.JSON(), nullable=True))
    op.add_column('problems', sa.Column('correct_option', sa.String(length=100), nullable=True))

    # 2. Create diagnostic_assessments table
    op.create_table(
        'diagnostic_assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='IN_PROGRESS', nullable=False),
        sa.Column('total_questions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('answered_questions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('correct_answers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_diagnostic_assessments_id'), 'diagnostic_assessments', ['id'], unique=False)
    op.create_index(op.f('ix_diagnostic_assessments_user_id'), 'diagnostic_assessments', ['user_id'], unique=False)
    op.create_index(op.f('ix_diagnostic_assessments_status'), 'diagnostic_assessments', ['status'], unique=False)

    # 3. Create diagnostic_responses table
    op.create_table(
        'diagnostic_responses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('selected_answer', sa.String(length=255), nullable=True),
        sa.Column('is_correct', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['diagnostic_assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_diagnostic_responses_id'), 'diagnostic_responses', ['id'], unique=False)
    op.create_index(op.f('ix_diagnostic_responses_assessment_id'), 'diagnostic_responses', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_diagnostic_responses_problem_id'), 'diagnostic_responses', ['problem_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_diagnostic_responses_problem_id'), table_name='diagnostic_responses')
    op.drop_index(op.f('ix_diagnostic_responses_assessment_id'), table_name='diagnostic_responses')
    op.drop_index(op.f('ix_diagnostic_responses_id'), table_name='diagnostic_responses')
    op.drop_table('diagnostic_responses')

    op.drop_index(op.f('ix_diagnostic_assessments_status'), table_name='diagnostic_assessments')
    op.drop_index(op.f('ix_diagnostic_assessments_user_id'), table_name='diagnostic_assessments')
    op.drop_index(op.f('ix_diagnostic_assessments_id'), table_name='diagnostic_assessments')
    op.drop_table('diagnostic_assessments')

    op.drop_column('problems', 'correct_option')
    op.drop_column('problems', 'options')
    op.drop_column('problems', 'question_type')
