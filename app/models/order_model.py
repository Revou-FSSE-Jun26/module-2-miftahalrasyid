from app.extensions import db
import datetime as dt
from sqlalchemy import CheckConstraint, func
from enum import Enum


class OrderStatus(Enum):
    PENDING   = "PENDING"
    PROCESSED = "PROCESSED"
    ACCEPTED  = "ACCEPTED"
    SHIPPING  = "SHIPPING"
    DELIVERED = "DELIVERED"


class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        CheckConstraint('lower(name) = name', name='orders_name_check'),
    )

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    name       = db.Column(db.String(150), nullable=False)
    status     = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    total      = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    products = db.relationship('Product', secondary='order_items', backref='orders', viewonly=True)

    def to_dict(self):
        return {
            "id"        : self.id,
            "name"      : self.name,
            "status"    : self.status.value,
            "total"     : float(self.total),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
