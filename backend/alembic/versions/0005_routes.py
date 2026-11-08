"""routes

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('routes',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('classroom_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_routes_org_id'), 'routes', ['org_id'], unique=False)
    op.create_index(op.f('ix_routes_classroom_id'), 'routes', ['classroom_id'], unique=False)

    op.create_table('route_stops',
    sa.Column('route_id', sa.UUID(), nullable=False),
    sa.Column('assignment_id', sa.UUID(), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('route_id', 'order_index'),
    sa.UniqueConstraint('assignment_id'),
    )
    op.create_index(op.f('ix_route_stops_route_id'), 'route_stops', ['route_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_route_stops_route_id'), table_name='route_stops')
    op.drop_table('route_stops')
    op.drop_index(op.f('ix_routes_classroom_id'), table_name='routes')
    op.drop_index(op.f('ix_routes_org_id'), table_name='routes')
    op.drop_table('routes')
