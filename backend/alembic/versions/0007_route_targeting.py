"""route targeting

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('routes', sa.Column('target_student_ids', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('routes', 'target_student_ids')
