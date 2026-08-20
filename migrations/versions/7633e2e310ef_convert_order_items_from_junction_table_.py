"""convert order_items from junction table to normal model with id quantity compound_price

Revision ID: 7633e2e310ef
Revises: fb1b2de14c14
Create Date: 2026-08-18 10:02:56.080249

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7633e2e310ef'
down_revision = 'fb1b2de14c14'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Drop composite primary key lama (order_id, product_id)
    op.execute('ALTER TABLE order_items DROP CONSTRAINT IF EXISTS pk_order_items')
    op.execute('ALTER TABLE order_items DROP CONSTRAINT IF EXISTS order_items_pkey')

    # 2. Tambah kolom id sebagai SERIAL (auto-increment) — otomatis isi untuk row baru
    op.add_column('order_items', sa.Column('id', sa.Integer(), sa.Identity(), nullable=False))

    # 3. Tambah kolom quantity & compound_price sebagai NULLABLE dulu
    op.add_column('order_items', sa.Column('quantity', sa.Integer(), nullable=True))
    op.add_column('order_items', sa.Column('compound_price', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('order_items', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 4. Backfill data existing: quantity=1, compound_price=100
    op.execute("UPDATE order_items SET quantity = 1, compound_price = 100 WHERE quantity IS NULL")

    # 5. Setelah backfill, set NOT NULL constraint
    op.alter_column('order_items', 'quantity', nullable=False)
    op.alter_column('order_items', 'compound_price', nullable=False)

    # 6. Set id sebagai primary key baru
    op.create_primary_key('pk_order_items', 'order_items', ['id'])

    # 7. Tambah unique constraint pada (order_id, product_id)
    op.create_unique_constraint('uq_order_product', 'order_items', ['order_id', 'product_id'])


def downgrade():
    # Balik ke junction table
    op.drop_constraint('uq_order_product', 'order_items', type_='unique')
    op.drop_constraint('pk_order_items', 'order_items', type_='primary')
    op.drop_column('order_items', 'deleted_at')
    op.drop_column('order_items', 'compound_price')
    op.drop_column('order_items', 'quantity')
    op.drop_column('order_items', 'id')

    # Restore composite PK
    op.create_primary_key('pk_order_items', 'order_items', ['order_id', 'product_id'])
