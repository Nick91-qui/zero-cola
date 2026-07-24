"""create_exams_attempts_skills_tables

Revision ID: 9a8f7b6c5d4e
Revises: 8c7e7c2e4e00
Create Date: 2026-07-24 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a8f7b6c5d4e'
down_revision: Union[str, None] = '8c7e7c2e4e00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create exams table
    op.create_table(
        'exams',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('teacher_id', sa.UUID(), nullable=False),
        sa.Column('class_id', sa.String(length=100), nullable=True),
        sa.Column('omr_template_id', sa.UUID(), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('max_score', sa.Numeric(precision=5, scale=2), nullable=False, server_default='10.00'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Create questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('statement', sa.String(), nullable=True),
        sa.Column('correct_option', sa.String(length=10), nullable=True),
        sa.Column('weight', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create skills table
    op.create_table(
        'skills',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=True),
        sa.Column('grade_level', sa.String(length=50), nullable=True),
        sa.Column('curriculum', sa.String(length=50), nullable=True, server_default='BNCC'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skills_code'), 'skills', ['code'], unique=True)

    # 4. Create question_skills table
    op.create_table(
        'question_skills',
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('skill_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('question_id', 'skill_id')
    )

    # 5. Create attempts table
    op.create_table(
        'attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=True),
        sa.Column('student_code', sa.String(length=5), nullable=True),
        sa.Column('omr_scan_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='graded'),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('incorrect_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accuracy_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('raw_score', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('final_score', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['omr_scan_id'], ['omr_scans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Create attempt_answers table
    op.create_table(
        'attempt_answers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('attempt_id', sa.UUID(), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=True),
        sa.Column('selected_option', sa.String(length=10), nullable=True),
        sa.Column('correct_option', sa.String(length=10), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['attempt_id'], ['attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Add columns and foreign keys to omr_templates
    op.add_column('omr_templates', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('omr_templates', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('omr_templates', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        'fk_omr_templates_exam_id_exams',
        'omr_templates',
        'exams',
        ['exam_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_exams_omr_template_id_omr_templates',
        'exams',
        'omr_templates',
        ['omr_template_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_exams_omr_template_id_omr_templates', 'exams', type_='foreignkey')
    op.drop_constraint('fk_omr_templates_exam_id_exams', 'omr_templates', type_='foreignkey')
    op.drop_column('omr_templates', 'deleted_at')
    op.drop_column('omr_templates', 'is_active')
    op.drop_column('omr_templates', 'title')

    op.drop_table('attempt_answers')
    op.drop_table('attempts')
    op.drop_table('question_skills')
    op.drop_index(op.f('ix_skills_code'), table_name='skills')
    op.drop_table('skills')
    op.drop_table('questions')
    op.drop_table('exams')
