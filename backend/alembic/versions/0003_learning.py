"""learning

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('assignments',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('classroom_id', sa.UUID(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('submission_types', sa.String(length=60), nullable=False),
    sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assignments_org_id'), 'assignments', ['org_id'], unique=False)
    op.create_index(op.f('ix_assignments_classroom_id'), 'assignments', ['classroom_id'], unique=False)

    op.create_table('assignment_targets',
    sa.Column('assignment_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assignment_id', 'student_id'),
    )
    op.create_index(op.f('ix_assignment_targets_assignment_id'), 'assignment_targets', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_assignment_targets_student_id'), 'assignment_targets', ['student_id'], unique=False)

    op.create_table('submissions',
    sa.Column('assignment_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('text_content', sa.Text(), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assignment_id', 'student_id'),
    )
    op.create_index(op.f('ix_submissions_assignment_id'), 'submissions', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_submissions_student_id'), 'submissions', ['student_id'], unique=False)

    op.create_table('submission_files',
    sa.Column('submission_id', sa.UUID(), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('path', sa.String(length=300), nullable=False),
    sa.Column('original_name', sa.String(length=200), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_submission_files_submission_id'), 'submission_files', ['submission_id'], unique=False)

    op.create_table('reviews',
    sa.Column('submission_id', sa.UUID(), nullable=False),
    sa.Column('teacher_id', sa.UUID(), nullable=False),
    sa.Column('score', sa.Integer(), nullable=True),
    sa.Column('feedback_text', sa.Text(), nullable=True),
    sa.Column('request_redo', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reviews_submission_id'), 'reviews', ['submission_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reviews_submission_id'), table_name='reviews')
    op.drop_table('reviews')
    op.drop_index(op.f('ix_submission_files_submission_id'), table_name='submission_files')
    op.drop_table('submission_files')
    op.drop_index(op.f('ix_submissions_student_id'), table_name='submissions')
    op.drop_index(op.f('ix_submissions_assignment_id'), table_name='submissions')
    op.drop_table('submissions')
    op.drop_index(op.f('ix_assignment_targets_student_id'), table_name='assignment_targets')
    op.drop_index(op.f('ix_assignment_targets_assignment_id'), table_name='assignment_targets')
    op.drop_table('assignment_targets')
    op.drop_index(op.f('ix_assignments_classroom_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_org_id'), table_name='assignments')
    op.drop_table('assignments')
