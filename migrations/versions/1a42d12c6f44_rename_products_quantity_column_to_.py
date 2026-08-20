"""rename products quantity column to stock and update constraint

Revision ID: 1a42d12c6f44
Revises: 9a575b777f47
Create Date: 2026-08-18 20:26:16.697929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a42d12c6f44'
down_revision = '9a575b777f47'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Drop the old constraint
    op.drop_constraint('products_quantity_check', 'products', type_='check')

    # 2. Rename column (preserves existing data)
    op.alter_column('products', 'quantity', new_column_name='stock')

    # 3. Create new constraint with correct name
    op.create_check_constraint('products_stock_check', 'products', 'stock >= 0')


def downgrade():
    # 1. Drop new constraint
    op.drop_constraint('products_stock_check', 'products', type_='check')

    # 2. Rename column back
    op.alter_column('products', 'stock', new_column_name='quantity')

    # 3. Restore old constraint
    op.create_check_constraint('products_quantity_check', 'products', 'quantity >= 0')
