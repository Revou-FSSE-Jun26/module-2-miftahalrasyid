"""add uuid column to products

Revision ID: 06c257caa915
Revises: 29d20ad1e7a2
Create Date: 2026-08-22 18:02:26.879505

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '06c257caa915'
down_revision = '29d20ad1e7a2'
branch_labels = None
depends_on = None


def upgrade():
    # Add uuid as nullable first
    op.add_column('products', sa.Column('uuid', sa.String(length=36), nullable=True))

    # Backfill existing rows with generated UUIDs
    op.execute("UPDATE products SET uuid = gen_random_uuid()::text WHERE uuid IS NULL")

    # Now set NOT NULL and unique constraint
    op.alter_column('products', 'uuid', nullable=False)
    op.create_unique_constraint('uq_products_uuid', 'products', ['uuid'])


def downgrade():
    op.drop_constraint('uq_products_uuid', 'products', type_='unique')
    op.drop_column('products', 'uuid')
