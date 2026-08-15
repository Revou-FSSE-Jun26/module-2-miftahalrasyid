from app import db
import datetime as dt
from enum import Enum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import func
import hashlib

class UserRole(Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(75),nullable=False)
    role = db.Column(ARRAY(db.Enum(UserRole, name='userrole')), nullable=False, default=[UserRole.BUYER])
    email = db.Column(db.String(150), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    provider = db.Column(db.String(50), nullable=False, default='password_hash')
    provider_key = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    deleted_at = db.Column(db.DateTime(timezone=True))

    @property
    def password(self):
        """
        Getter: Dipanggil saat sistem mencoba membaca .password (misal saat GET).
        Kita selalu return None agar password tidak pernah bocor keluar dari memori.
        """
        return None

    @password.setter
    def password(self, value):
        """
        Setter: Otomatis terpicu saat Flask-Smorest mengeksekusi User(password="...").
        Data password polos langsung di-hash menggunakan SHA-256 andalan Anda 
        dan langsung disimpan ke kolom asli database 'provider_key'.
        """
        if value:
            self.provider_key = hashlib.sha256(value.encode('utf-8')).hexdigest()

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": [r.value for r in self.role] if self.role else [],
            "email": self.email,
            "age": self.age,
            "is_active": self.is_active,
            "provider": self.provider,
            "provider_key": self.provider_key,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
