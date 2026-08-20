"""change provider column from string to enum authprovider

Revision ID: 9a575b777f47
Revises: 7633e2e310ef
Create Date: 2026-08-18 12:37:59.282074

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a575b777f47'
down_revision = '7633e2e310ef'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create the enum type in PostgreSQL
    authprovider_enum = sa.Enum('PASSWORD_HASH', 'GOOGLE_OAUTH', name='authprovider')
    authprovider_enum.create(op.get_bind(), checkfirst=True)

    # 2. Drop existing default (it's a varchar default that can't auto-cast to enum)
    op.execute("ALTER TABLE users ALTER COLUMN provider DROP DEFAULT")

    # 3. Convert existing data: any existing value -> 'PASSWORD_HASH'
    op.execute("UPDATE users SET provider = 'PASSWORD_HASH' WHERE provider IS NOT NULL")

    # 4. Alter column type using USING clause for PostgreSQL cast
    op.execute(
        "ALTER TABLE users ALTER COLUMN provider TYPE authprovider "
        "USING provider::authprovider"
    )

    # 5. Set new default as enum value
    op.execute("ALTER TABLE users ALTER COLUMN provider SET DEFAULT 'PASSWORD_HASH'")


def downgrade():
    # 1. Convert back to varchar
    op.execute("ALTER TABLE users ALTER COLUMN provider TYPE VARCHAR(50) USING provider::text")

    # 2. Set old default
    op.execute("ALTER TABLE users ALTER COLUMN provider SET DEFAULT 'password_hash'")

    # 3. Drop the enum type
    sa.Enum(name='authprovider').drop(op.get_bind(), checkfirst=True)
