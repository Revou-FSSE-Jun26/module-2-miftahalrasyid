from app.extensions import db
from sqlalchemy import func


class Address(db.Model):
    __tablename__ = 'addresses'

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    label           = db.Column(db.String(50), nullable=False)  # e.g. "Home", "Office"
    recipient_name  = db.Column(db.String(150), nullable=False)
    phone           = db.Column(db.String(20), nullable=False)
    address_line    = db.Column(db.String(300), nullable=False)
    city            = db.Column(db.String(100), nullable=False)
    province        = db.Column(db.String(100), nullable=False)
    postal_code     = db.Column(db.String(10), nullable=False)
    is_default      = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime(timezone=True), server_default=func.now())

    user = db.relationship('User', backref=db.backref('addresses', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "label": self.label,
            "recipient_name": self.recipient_name,
            "phone": self.phone,
            "address_line": self.address_line,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
