"""Add slug, images, updated_at to products

Revision ID: 29d20ad1e7a2
Revises: e6f0237835c7
Create Date: 2026-08-22 14:47:03.644750

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '29d20ad1e7a2'
down_revision = 'e6f0237835c7'
branch_labels = None
depends_on = None


def upgrade():
    # Add slug as nullable first
    op.add_column('products', sa.Column('slug', sa.String(length=150), nullable=True))
    op.add_column('products', sa.Column('images', postgresql.ARRAY(sa.String(length=150)), nullable=True))
    op.add_column('products', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    # Backfill slug for existing rows using the product id
    op.execute("UPDATE products SET slug = 'product-' || id WHERE slug IS NULL")

    # Now set NOT NULL and unique constraint
    op.alter_column('products', 'slug', nullable=False)
    op.create_unique_constraint('uq_products_slug', 'products', ['slug'])


def downgrade():
    op.drop_constraint('uq_products_slug', 'products', type_='unique')
    op.drop_column('products', 'updated_at')
    op.drop_column('products', 'images')
    op.drop_column('products', 'slug')
