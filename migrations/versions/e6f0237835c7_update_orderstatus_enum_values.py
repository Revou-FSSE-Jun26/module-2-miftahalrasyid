"""update orderstatus enum values

Revision ID: e6f0237835c7
Revises: d95589515a54
Create Date: 2026-08-21 00:03:54.613914

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e6f0237835c7'
down_revision = 'd95589515a54'
branch_labels = None
depends_on = None


def upgrade():
    # Add new enum values to orderstatus type
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'PAID'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'CANCELED'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'COMPLETED'")


def downgrade():
    # PostgreSQL doesn't support removing enum values directly.
    # To fully downgrade, you'd need to recreate the type.
    # Since this is additive only, downgrade is a no-op.
    pass
