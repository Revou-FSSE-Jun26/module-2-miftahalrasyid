from app.extensions import db
from sqlalchemy.sql import func


class Order_item(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = (
        db.UniqueConstraint('order_id', 'product_id', name='uq_order_product'),
    )

    id             = db.Column(db.Integer, primary_key=True)
    product_id     = db.Column("product_id", db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    order_id       = db.Column("order_id", db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    quantity       = db.Column(db.Integer, nullable=False)
    compound_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at     = db.Column("created_at", db.DateTime(timezone=True), server_default=func.now())
    deleted_at     = db.Column(db.DateTime(timezone=True), nullable=True)
