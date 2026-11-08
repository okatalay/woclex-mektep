"""classes

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('classrooms',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('teacher_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('join_code', sa.String(length=24), nullable=False),
    sa.Column('join_enabled', sa.Boolean(), nullable=False),
    sa.Column('is_archived', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('join_code'),
    )
    op.create_index(op.f('ix_classrooms_org_id'), 'classrooms', ['org_id'], unique=False)
    op.create_index(op.f('ix_classrooms_teacher_id'), 'classrooms', ['teacher_id'], unique=False)

    op.create_table('enrollments',
    sa.Column('classroom_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('classroom_id', 'student_id'),
    )
    op.create_index(op.f('ix_enrollments_classroom_id'), 'enrollments', ['classroom_id'], unique=False)
    op.create_index(op.f('ix_enrollments_student_id'), 'enrollments', ['student_id'], unique=False)

    op.create_table('guardian_links',
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('guardian_id', sa.UUID(), nullable=False),
    sa.Column('relation', sa.String(length=40), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['guardian_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'guardian_id'),
    )
    op.create_index(op.f('ix_guardian_links_student_id'), 'guardian_links', ['student_id'], unique=False)
    op.create_index(op.f('ix_guardian_links_guardian_id'), 'guardian_links', ['guardian_id'], unique=False)

    op.create_table('guardian_invites',
    sa.Column('token_hash', sa.String(length=128), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('relation_hint', sa.String(length=40), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash'),
    )
    op.create_index(op.f('ix_guardian_invites_org_id'), 'guardian_invites', ['org_id'], unique=False)
    op.create_index(op.f('ix_guardian_invites_student_id'), 'guardian_invites', ['student_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_guardian_invites_student_id'), table_name='guardian_invites')
    op.drop_index(op.f('ix_guardian_invites_org_id'), table_name='guardian_invites')
    op.drop_table('guardian_invites')
    op.drop_index(op.f('ix_guardian_links_guardian_id'), table_name='guardian_links')
    op.drop_index(op.f('ix_guardian_links_student_id'), table_name='guardian_links')
    op.drop_table('guardian_links')
    op.drop_index(op.f('ix_enrollments_student_id'), table_name='enrollments')
    op.drop_index(op.f('ix_enrollments_classroom_id'), table_name='enrollments')
    op.drop_table('enrollments')
    op.drop_index(op.f('ix_classrooms_teacher_id'), table_name='classrooms')
    op.drop_index(op.f('ix_classrooms_org_id'), table_name='classrooms')
    op.drop_table('classrooms')
