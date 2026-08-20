from app.extensions import db
import datetime as dt
from enum import Enum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib


class UserRole(Enum):
    BUYER      = "BUYER"
    SELLER     = "SELLER"
    ADMIN      = "ADMIN"
    SUPERADMIN = "SUPERADMIN"


class AuthProvider(Enum):
    PASSWORD_HASH = "PASSWORD_HASH"
    GOOGLE_OAUTH  = "GOOGLE_OAUTH"


class User(db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(75), nullable=False)
    roles         = db.Column(ARRAY(db.Enum(UserRole, name='userrole')), nullable=False, default=[UserRole.BUYER])
    email        = db.Column(db.String(150), unique=True, nullable=False)
    age          = db.Column(db.Integer, nullable=False)
    is_active    = db.Column(db.Boolean, default=False)
    provider     = db.Column(db.Enum(AuthProvider, name='authprovider'), nullable=False, default=AuthProvider.PASSWORD_HASH)
    provider_key = db.Column(db.String(255), nullable=False)
    created_at   = db.Column(db.DateTime(timezone=True), server_default=func.now())
    deleted_at   = db.Column(db.DateTime(timezone=True))

    @property
    def password(self):
        """
        Getter: Called when the system tries to read .password (e.g. during GET).
        Always returns None so the password never leaks out of memory.
        """
        return None

    @password.setter
    def password(self, value):
        """
        Setter: Triggered automatically when Flask-Smorest executes User(password="...").
        The plain password is hashed using PBKDF2-SHA256 (via Werkzeug) and stored
        in the 'provider_key' database column.
        """
        if value:
            self.provider_key = generate_password_hash(value)

    def verify_password(self, password):
        """
        Verify a password against the stored hash.
        Supports Werkzeug PBKDF2 (new) and SHA256 (old) for backward compatibility.
        Returns True if password matches, False otherwise.
        """
        if not self.provider_key or self.provider == AuthProvider.GOOGLE_OAUTH:
            return False
        
        try:
            # Try Werkzeug hash first (new format: pbkdf2:sha256:...)
            if self.provider_key.startswith(('pbkdf2:', 'scrypt:')):
                return check_password_hash(self.provider_key, password)
            # Try legacy bcrypt format ($2b$...)
            if self.provider_key.startswith('$2b$') or self.provider_key.startswith('$2a$'):
                # Can't verify bcrypt without the library — fall through to SHA256
                pass
            # SHA256 fallback (old format)
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return password_hash == self.provider_key
        except Exception:
            return False
    
    def upgrade_password_hash(self, password):
        """
        Upgrade SHA256 hash to Werkzeug PBKDF2 and save to database.
        Should be called after verifying old password.
        """
        if self.provider == AuthProvider.PASSWORD_HASH:
            self.password = password

    def to_dict(self):
        return {
            "id"          : self.id,
            "username"    : self.username,
            "roles"        : [r.value for r in self.roles] if self.roles else [],
            "email"       : self.email,
            "age"         : self.age,
            "is_active"   : self.is_active,
            "provider"    : self.provider.value if self.provider else None,
            "provider_key": self.provider_key,
            "created_at"  : self.created_at.isoformat() if self.created_at else None
        }
