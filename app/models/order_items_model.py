from app.extensions import db
from sqlalchemy.sql import func


class Order_item(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = (
        db.UniqueConstraint('order_id', 'seller_product_id', name='uq_order_seller_product'),
    )

    id                = db.Column(db.Integer, primary_key=True)
    # An order line points at a specific seller's offer (listing), not the
    # abstract catalog product — this preserves which seller/price was bought.
    seller_product_id = db.Column("seller_product_id", db.Integer, db.ForeignKey("seller_products.id", ondelete="CASCADE"), nullable=False)
    order_id          = db.Column("order_id", db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    quantity          = db.Column(db.Integer, nullable=False)
    compound_price    = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at        = db.Column("created_at", db.DateTime(timezone=True), server_default=func.now())
    deleted_at        = db.Column(db.DateTime(timezone=True), nullable=True)
