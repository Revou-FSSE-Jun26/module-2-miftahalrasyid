from app.extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint, func


class CartItem(db.Model):
    """
    A single line in a user's cart.

    The user *is* the cart — there is no separate `cart` header row. Each row is
    one seller listing the user intends to buy, scoped to that user (1:N
    users -> cart_items). Like order lines, a cart line references a specific
    seller's listing (seller_products.id), not the abstract catalog product, so
    the chosen seller/price is preserved. Price is NOT snapshotted here: the cart
    always reads the live listing price. Snapshotting belongs to order_items at
    checkout.

    UNIQUE(user_id, seller_product_id): adding the same listing bumps quantity
    instead of creating a duplicate row.
    """
    __tablename__ = 'cart_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='cart_items_quantity_check'),
        UniqueConstraint('user_id', 'seller_product_id', name='uq_cart_user_listing'),
    )

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    seller_product_id = db.Column(db.Integer, db.ForeignKey('seller_products.id', ondelete='CASCADE'), nullable=False)
    quantity          = db.Column(db.Integer, nullable=False, default=1)
    created_at        = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at        = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # The seller listing this cart line points at.
    listing = db.relationship('SellerProduct', backref='cart_items')

    def to_dict(self, allowed_fields=None):
        data = {
            'id'               : self.id,
            'user_id'          : self.user_id,
            'seller_product_id': self.seller_product_id,
            'quantity'         : self.quantity,
            'created_at'       : self.created_at.isoformat() if self.created_at else None,
            'updated_at'       : self.updated_at.isoformat() if self.updated_at else None,
        }
        if allowed_fields:
            return {k: v for k, v in data.items() if k in allowed_fields}
        return data
