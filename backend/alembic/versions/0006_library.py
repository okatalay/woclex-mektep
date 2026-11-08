"""library

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('assignment_attachments',
    sa.Column('assignment_id', sa.UUID(), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('path', sa.String(length=300), nullable=False),
    sa.Column('original_name', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assignment_attachments_assignment_id'), 'assignment_attachments', ['assignment_id'], unique=False)

    op.create_table('library_items',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_library_items_org_id'), 'library_items', ['org_id'], unique=False)

    op.create_table('library_item_files',
    sa.Column('library_item_id', sa.UUID(), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('path', sa.String(length=300), nullable=False),
    sa.Column('original_name', sa.String(length=200), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['library_item_id'], ['library_items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_library_item_files_library_item_id'), 'library_item_files', ['library_item_id'], unique=False)

    op.create_table('route_templates',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_route_templates_org_id'), 'route_templates', ['org_id'], unique=False)

    op.create_table('route_template_stops',
    sa.Column('template_id', sa.UUID(), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('submission_types', sa.String(length=60), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['template_id'], ['route_templates.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('template_id', 'order_index'),
    )
    op.create_index(op.f('ix_route_template_stops_template_id'), 'route_template_stops', ['template_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_route_template_stops_template_id'), table_name='route_template_stops')
    op.drop_table('route_template_stops')
    op.drop_index(op.f('ix_route_templates_org_id'), table_name='route_templates')
    op.drop_table('route_templates')
    op.drop_index(op.f('ix_library_item_files_library_item_id'), table_name='library_item_files')
    op.drop_table('library_item_files')
    op.drop_index(op.f('ix_library_items_org_id'), table_name='library_items')
    op.drop_table('library_items')
    op.drop_index(op.f('ix_assignment_attachments_assignment_id'), table_name='assignment_attachments')
    op.drop_table('assignment_attachments')
