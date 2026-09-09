"""split products into catalog + seller_products, repoint order_items

Revision ID: a1b2c3d4e5f6
Revises: c4376e96a7c7
Create Date: 2026-09-09

Splits the monolithic `products` table into:
  - `products`      : catalog spec (brand/name/model/color/size/barcode/specs)
  - `seller_products`: per-seller listing (price/stock/status/sku/images/title/slug)
and repoints `order_items.product_id` -> `order_items.seller_product_id`.

Reversible. NOTE (documented in seller_products_design.md): once a catalog product
has more than one seller listing, downgrade cannot losslessly collapse back to a
single row — the downgrade keeps the listing with the lowest id and discards the rest.
Take a DB backup before upgrading.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'b7c8d9e0f1a2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


PRODUCT_STATUS = postgresql.ENUM(
    'PENDING', 'ACTIVE', 'INACTIVE', 'SUSPENDED', 'REJECTED',
    name='productstatus', create_type=False,
)


def upgrade():
    bind = op.get_bind()

    # -- 1. Create seller_products -------------------------------------------
    op.create_table(
        'seller_products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('stock', sa.Integer(), server_default='0'),
        sa.Column('status', PRODUCT_STATUS, nullable=False, server_default='PENDING'),
        sa.Column('sku', sa.String(length=50), nullable=True),
        sa.Column('images', postgresql.ARRAY(sa.String(length=150)), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('slug'),
        sa.CheckConstraint('stock >= 0', name='seller_products_stock_check'),
        sa.UniqueConstraint('product_id', 'user_id', name='uq_seller_product_seller'),
    )

    # -- 2. Migrate each existing products row into one seller_products row ---
    # The catalog product keeps its id; the listing carries the seller fields.
    # title := products.name ; listing.slug := products.slug (both unique-safe 1:1).
    bind.execute(sa.text("""
        INSERT INTO seller_products
            (uuid, product_id, user_id, title, slug, price, stock, status, sku, images, created_at)
        SELECT
            gen_random_uuid()::text,
            p.id, p.user_id, p.name, p.slug,
            COALESCE(p.price, 0), COALESCE(p.stock, 0),
            p.status, p.sku, p.images, p.created_at
        FROM products p
    """))

    # -- 3. Repoint order_items.product_id -> seller_product_id ---------------
    op.add_column('order_items', sa.Column('seller_product_id', sa.Integer(), nullable=True))
    # Each old order_item.product_id maps to the single seller_products row we
    # just created for that catalog product.
    bind.execute(sa.text("""
        UPDATE order_items oi
        SET seller_product_id = sp.id
        FROM seller_products sp
        WHERE sp.product_id = oi.product_id
    """))

    op.drop_constraint('uq_order_product', 'order_items', type_='unique')
    op.drop_constraint('order_items_product_id_fkey', 'order_items', type_='foreignkey')
    op.drop_column('order_items', 'product_id')
    op.alter_column('order_items', 'seller_product_id', nullable=False)
    op.create_foreign_key(
        'order_items_seller_product_id_fkey', 'order_items', 'seller_products',
        ['seller_product_id'], ['id'], ondelete='CASCADE',
    )
    op.create_unique_constraint(
        'uq_order_seller_product', 'order_items', ['order_id', 'seller_product_id'],
    )

    # -- 4. Slim the products (catalog) table --------------------------------
    op.drop_constraint('products_stock_check', 'products', type_='check')
    # products.slug had a unique constraint/index — drop it (slug moved to listing)
    op.drop_constraint('products_user_id_fkey', 'products', type_='foreignkey')
    # 'updated_at' existed on the old products table but is being retired entirely
    # (not carried to the catalog or to seller_products).
    for col in ('user_id', 'price', 'stock', 'status', 'sku', 'images', 'slug', 'updated_at'):
        _drop_column_if_exists(bind, 'products', col)

    # Widen brand/name to catalog sizes and add spec columns (added nullable in
    # Phase 1 model; ensure they exist for older DBs too).
    op.alter_column('products', 'brand', type_=sa.String(length=100))
    op.alter_column('products', 'name', type_=sa.String(length=255))
    for col, coltype in (
        ('model', sa.String(length=255)),
        ('color', sa.String(length=100)),
        ('size', sa.String(length=100)),
        ('barcode', sa.String(length=50)),
    ):
        _add_column_if_missing(bind, 'products', col, coltype)
    _add_column_if_missing(bind, 'products', 'specifications', postgresql.JSONB())

    # Partial-unique barcode: unique only when NOT NULL.
    op.create_index(
        'uq_products_barcode', 'products', ['barcode'],
        unique=True, postgresql_where=sa.text('barcode IS NOT NULL'),
    )

    # Catalog TRIM + deleted_at checks.
    op.create_check_constraint('products_brand_trim_check', 'products', 'brand = TRIM(brand)')
    op.create_check_constraint('products_name_trim_check', 'products', 'name = TRIM(name)')
    op.create_check_constraint('products_model_trim_check', 'products', 'model IS NULL OR model = TRIM(model)')
    op.create_check_constraint('products_color_trim_check', 'products', 'color IS NULL OR color = TRIM(color)')
    op.create_check_constraint('products_size_trim_check', 'products', 'size IS NULL OR size = TRIM(size)')
    # NOTE: a deleted_at >= created_at check is intentionally NOT added — legacy
    # seeded rows can carry a deleted_at earlier than created_at and it adds no
    # real value. Kept out to avoid a migration failure on existing data.


def downgrade():
    bind = op.get_bind()

    # -- Reverse 4: restore seller columns on products -----------------------
    for name in (
        'products_brand_trim_check', 'products_name_trim_check', 'products_model_trim_check',
        'products_color_trim_check', 'products_size_trim_check',
    ):
        op.drop_constraint(name, 'products', type_='check')
    op.drop_index('uq_products_barcode', table_name='products')

    op.add_column('products', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('price', sa.Numeric(10, 2), server_default='0'))
    op.add_column('products', sa.Column('stock', sa.Integer(), server_default='0'))
    op.add_column('products', sa.Column('status', PRODUCT_STATUS, server_default='PENDING'))
    op.add_column('products', sa.Column('sku', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('images', postgresql.ARRAY(sa.String(length=150)), nullable=True))
    op.add_column('products', sa.Column('slug', sa.String(length=150), nullable=True))
    # Restore the pre-split updated_at column on products (guard: an older run of
    # this migration may have left it in place).
    _add_column_if_missing(bind, 'products', 'updated_at', sa.DateTime(timezone=True))

    # Collapse listings back onto catalog: pick the lowest-id listing per product.
    bind.execute(sa.text("""
        UPDATE products p
        SET user_id = sp.user_id,
            price   = sp.price,
            stock   = sp.stock,
            status  = sp.status,
            sku     = sp.sku,
            images  = sp.images,
            slug    = sp.slug
        FROM (
            SELECT DISTINCT ON (product_id) product_id, id, user_id, price, stock, status, sku, images, slug
            FROM seller_products
            ORDER BY product_id, id ASC
        ) sp
        WHERE sp.product_id = p.id
    """))

    # Fallback slug for any catalog row with no listing.
    bind.execute(sa.text("UPDATE products SET slug = 'product-' || id WHERE slug IS NULL"))
    op.alter_column('products', 'slug', nullable=False)
    op.alter_column('products', 'user_id', nullable=False)
    op.alter_column('products', 'price', nullable=False)
    op.alter_column('products', 'status', nullable=False)
    op.create_unique_constraint('products_slug_key', 'products', ['slug'])
    op.create_foreign_key('products_user_id_fkey', 'products', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_check_constraint('products_stock_check', 'products', 'stock >= 0')
    op.alter_column('products', 'brand', type_=sa.String(length=150))
    op.alter_column('products', 'name', type_=sa.String(length=150))

    # -- Reverse 3: restore order_items.product_id ---------------------------
    op.add_column('order_items', sa.Column('product_id', sa.Integer(), nullable=True))
    bind.execute(sa.text("""
        UPDATE order_items oi
        SET product_id = sp.product_id
        FROM seller_products sp
        WHERE sp.id = oi.seller_product_id
    """))
    op.drop_constraint('uq_order_seller_product', 'order_items', type_='unique')
    op.drop_constraint('order_items_seller_product_id_fkey', 'order_items', type_='foreignkey')
    op.drop_column('order_items', 'seller_product_id')
    op.alter_column('order_items', 'product_id', nullable=False)
    op.create_foreign_key('order_items_product_id_fkey', 'order_items', 'products', ['product_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint('uq_order_product', 'order_items', ['order_id', 'product_id'])

    # -- Reverse 1: drop seller_products -------------------------------------
    op.drop_table('seller_products')


def _add_column_if_missing(bind, table, column, coltype):
    """Add a column only if it isn't already present (Phase 1 model may have created it)."""
    exists = bind.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name=:t AND column_name=:c"
    ), {"t": table, "c": column}).first()
    if not exists:
        op.add_column(table, sa.Column(column, coltype, nullable=True))


def _drop_column_if_exists(bind, table, column):
    """Drop a column only if it is present."""
    exists = bind.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name=:t AND column_name=:c"
    ), {"t": table, "c": column}).first()
    if exists:
        op.drop_column(table, column)
