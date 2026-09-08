"""replace products.is_active boolean with a status enum lifecycle

Adds a `productstatus` enum (PENDING/ACTIVE/INACTIVE/SUSPENDED/REJECTED) and a
`products.status` column, backfills it from the old `is_active` boolean
(is_active=true -> ACTIVE, otherwise -> INACTIVE), then drops `is_active`.

Revision ID: a1b2c3d4e5f6
Revises: c4376e96a7c7
Create Date: 2026-09-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c4376e96a7c7'
branch_labels = None
depends_on = None


PRODUCT_STATUS_VALUES = ('PENDING', 'ACTIVE', 'INACTIVE', 'SUSPENDED', 'REJECTED')


def upgrade():
    bind = op.get_bind()

    # 1. Create the enum type explicitly (checkfirst so re-runs are safe).
    product_status = postgresql.ENUM(*PRODUCT_STATUS_VALUES, name='productstatus')
    product_status.create(bind, checkfirst=True)

    # 2. Add the column as nullable first so we can backfill existing rows.
    op.add_column('products', sa.Column('status', product_status, nullable=True))

    # 3. Backfill from the old boolean: active rows -> ACTIVE, everything else
    #    (inactive or NULL) -> INACTIVE. Existing catalog stays visible/usable.
    op.execute(
        "UPDATE products SET status = CASE "
        "WHEN is_active IS TRUE THEN 'ACTIVE'::productstatus "
        "ELSE 'INACTIVE'::productstatus END"
    )

    # 4. Enforce NOT NULL now that every row has a value.
    op.alter_column('products', 'status', existing_type=product_status, nullable=False)

    # 5. Drop the now-redundant boolean.
    op.drop_column('products', 'is_active')


def downgrade():
    bind = op.get_bind()

    # 1. Re-add the boolean.
    op.add_column('products', sa.Column('is_active', sa.Boolean(), nullable=True))

    # 2. Reverse-map: ACTIVE -> true, anything else -> false.
    op.execute("UPDATE products SET is_active = (status = 'ACTIVE'::productstatus)")

    # 3. Drop the status column and the enum type.
    op.drop_column('products', 'status')
    product_status = postgresql.ENUM(*PRODUCT_STATUS_VALUES, name='productstatus')
    product_status.drop(bind, checkfirst=True)
