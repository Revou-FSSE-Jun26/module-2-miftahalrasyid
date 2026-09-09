from app.extensions import db
from uuid import uuid4
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import CheckConstraint, UniqueConstraint, func

# ProductStatus is reused as-is from the catalog product model. Its VALUES do not
# change in the split — the enum simply now describes a *listing's* lifecycle
# (PENDING/ACTIVE/INACTIVE/SUSPENDED/REJECTED) instead of the catalog product's.
from app.models.product_model import ProductStatus


class SellerProduct(db.Model):
    """
    A single seller's offer (listing) for a catalog `Product`.

    The catalog `products` row holds the shared spec (brand/name/model/...).
    Each seller creates their own `seller_products` row with their own
    price / stock / status / sku / images / title. One listing per seller per
    catalog product (enforced by the unique constraint below).
    """
    __tablename__ = 'seller_products'
    __table_args__ = (
        CheckConstraint('stock >= 0', name='seller_products_stock_check'),
        UniqueConstraint('product_id', 'user_id', name='uq_seller_product_seller'),
    )

    id          = db.Column(db.Integer, primary_key=True)
    uuid        = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    product_id  = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title       = db.Column(db.String(255), nullable=False)
    slug        = db.Column(db.String(255), nullable=False, unique=True)
    price       = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock       = db.Column(db.Integer, default=0)
    status      = db.Column(db.Enum(ProductStatus), nullable=False, default=ProductStatus.PENDING)
    sku         = db.Column(db.String(50), nullable=True)
    images      = db.Column(ARRAY(db.String(150)), nullable=True)
    created_at  = db.Column(db.DateTime(timezone=True), server_default=func.now())
    deleted_at  = db.Column(db.DateTime(timezone=True), nullable=True)

    # The catalog product this listing offers. `backref='listings'` gives
    # Product.listings for the reverse direction.
    catalog = db.relationship('Product', backref='listings')

    # The seller who owns this listing.
    seller = db.relationship('User', backref='seller_products')

    def to_dict(self, allowed_fields=None):
        data = {
            'id'         : self.id,
            'uuid'       : self.uuid,
            'product_id' : self.product_id,
            'seller_id'  : self.user_id,
            'title'      : self.title,
            'slug'       : self.slug,
            'price'      : float(self.price) if self.price is not None else None,
            'stock'      : self.stock,
            'status'     : self.status.value if self.status else None,
            'sku'        : self.sku,
            'images'     : self.images or [],
            'created_at' : self.created_at.isoformat() if self.created_at else None,
            'deleted_at' : self.deleted_at.isoformat() if self.deleted_at else None,
        }
        if allowed_fields:
            return {k: v for k, v in data.items() if k in allowed_fields}
        return data
