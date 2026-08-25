from app.extensions import db
import datetime as dt
from sqlalchemy import CheckConstraint, func
from enum import Enum


class OrderStatus(Enum):
    PENDING   = "PENDING"
    PAID      = "PAID"
    CANCELED  = "CANCELED"
    COMPLETED = "COMPLETED"


class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        CheckConstraint('lower(name) = name', name='orders_name_check'),
    )

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    address_id       = db.Column(db.Integer, db.ForeignKey('addresses.id', ondelete='SET NULL'), nullable=True)
    name             = db.Column(db.String(150), nullable=False)
    status           = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    subtotal         = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_percent = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    discount_amount  = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tax_percent      = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    tax_amount       = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total            = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    created_at       = db.Column(db.DateTime(timezone=True), server_default=func.now())
    deleted_at       = db.Column(db.DateTime(timezone=True), nullable=True)

    products = db.relationship('Product', secondary='order_items', backref='orders', viewonly=True)
    address  = db.relationship('Address', backref='orders')

    def to_dict(self, allowed_fields=None):
        data = {
            "id"               : self.id,
            "user_id"          : self.user_id,
            "address_id"       : self.address_id,
            "name"             : self.name,
            "status"           : self.status.value,
            "subtotal"         : float(self.subtotal),
            "discount_percent" : float(self.discount_percent),
            "discount_amount"  : float(self.discount_amount),
            "tax_percent"      : float(self.tax_percent),
            "tax_amount"       : float(self.tax_amount),
            "total"            : float(self.total),
            "created_at"       : self.created_at.isoformat() if self.created_at else None,
            "deleted_at"       : self.deleted_at.isoformat() if self.deleted_at else None,
        }
        if allowed_fields:
            return {k: v for k, v in data.items() if k in allowed_fields}
        return data
