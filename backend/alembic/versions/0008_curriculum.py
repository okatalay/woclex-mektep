"""curriculum, attendance, page tracking

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('curriculum_categories',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('org_id', 'kind', 'order_index'),
    )
    op.create_index(op.f('ix_curriculum_categories_org_id'), 'curriculum_categories', ['org_id'], unique=False)

    op.create_table('curriculum_items',
    sa.Column('category_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['curriculum_categories.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('category_id', 'order_index'),
    )
    op.create_index(op.f('ix_curriculum_items_category_id'), 'curriculum_items', ['category_id'], unique=False)

    op.create_table('curriculum_status',
    sa.Column('item_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('updated_by', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['curriculum_items.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('item_id', 'student_id'),
    )
    op.create_index(op.f('ix_curriculum_status_item_id'), 'curriculum_status', ['item_id'], unique=False)
    op.create_index(op.f('ix_curriculum_status_student_id'), 'curriculum_status', ['student_id'], unique=False)

    op.create_table('attendance_records',
    sa.Column('classroom_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('classroom_id', 'student_id', 'date'),
    )
    op.create_index(op.f('ix_attendance_records_classroom_id'), 'attendance_records', ['classroom_id'], unique=False)
    op.create_index(op.f('ix_attendance_records_student_id'), 'attendance_records', ['student_id'], unique=False)

    op.create_table('page_logs',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('log_date', sa.Date(), nullable=False),
    sa.Column('start_page', sa.Integer(), nullable=False),
    sa.Column('end_page', sa.Integer(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_page_logs_org_id'), 'page_logs', ['org_id'], unique=False)
    op.create_index(op.f('ix_page_logs_student_id'), 'page_logs', ['student_id'], unique=False)

    # Yeni izin kodu: mevcut owner/admin/teacher rollerine geriye dönük ekle (yeni kurumlar zaten
    # permissions.py'deki güncel SYSTEM_ROLES ile oluşuyor).
    op.execute("""
        INSERT INTO role_permissions (role_id, permission)
        SELECT id, 'tracking.manage' FROM roles
        WHERE system_key IN ('owner', 'admin', 'teacher')
        AND id NOT IN (SELECT role_id FROM role_permissions WHERE permission = 'tracking.manage')
    """)


def downgrade() -> None:
    op.execute("DELETE FROM role_permissions WHERE permission = 'tracking.manage'")
    op.drop_index(op.f('ix_page_logs_student_id'), table_name='page_logs')
    op.drop_index(op.f('ix_page_logs_org_id'), table_name='page_logs')
    op.drop_table('page_logs')
    op.drop_index(op.f('ix_attendance_records_student_id'), table_name='attendance_records')
    op.drop_index(op.f('ix_attendance_records_classroom_id'), table_name='attendance_records')
    op.drop_table('attendance_records')
    op.drop_index(op.f('ix_curriculum_status_student_id'), table_name='curriculum_status')
    op.drop_index(op.f('ix_curriculum_status_item_id'), table_name='curriculum_status')
    op.drop_table('curriculum_status')
    op.drop_index(op.f('ix_curriculum_items_category_id'), table_name='curriculum_items')
    op.drop_table('curriculum_items')
    op.drop_index(op.f('ix_curriculum_categories_org_id'), table_name='curriculum_categories')
    op.drop_table('curriculum_categories')
