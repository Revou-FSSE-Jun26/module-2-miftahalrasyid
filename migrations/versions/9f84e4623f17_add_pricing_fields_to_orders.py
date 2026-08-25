"""add pricing fields to orders

Revision ID: 9f84e4623f17
Revises: 0268dfcb6edb
Create Date: 2026-08-24 22:21:57.244444

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f84e4623f17'
down_revision = '0268dfcb6edb'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns as nullable first
    op.add_column('orders', sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orders', sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('orders', sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orders', sa.Column('tax_percent', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('orders', sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=True))

    # Backfill existing rows with defaults (subtotal=total, no discount, no tax)
    op.execute("UPDATE orders SET subtotal = total WHERE subtotal IS NULL")
    op.execute("UPDATE orders SET discount_percent = 0 WHERE discount_percent IS NULL")
    op.execute("UPDATE orders SET discount_amount = 0 WHERE discount_amount IS NULL")
    op.execute("UPDATE orders SET tax_percent = 0 WHERE tax_percent IS NULL")
    op.execute("UPDATE orders SET tax_amount = 0 WHERE tax_amount IS NULL")

    # Now set NOT NULL
    op.alter_column('orders', 'subtotal', nullable=False)
    op.alter_column('orders', 'discount_percent', nullable=False)
    op.alter_column('orders', 'discount_amount', nullable=False)
    op.alter_column('orders', 'tax_percent', nullable=False)
    op.alter_column('orders', 'tax_amount', nullable=False)

    # Widen total column precision
    op.alter_column('orders', 'total',
        existing_type=sa.NUMERIC(precision=10, scale=2),
        type_=sa.Numeric(precision=12, scale=2),
        existing_nullable=False)


def downgrade():
    op.alter_column('orders', 'total',
        existing_type=sa.Numeric(precision=12, scale=2),
        type_=sa.NUMERIC(precision=10, scale=2),
        existing_nullable=False)
    op.drop_column('orders', 'tax_amount')
    op.drop_column('orders', 'tax_percent')
    op.drop_column('orders', 'discount_amount')
    op.drop_column('orders', 'discount_percent')
    op.drop_column('orders', 'subtotal')
