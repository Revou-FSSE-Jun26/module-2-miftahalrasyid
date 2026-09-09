from app.extensions import db
import datetime as dt
from uuid import uuid4
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import CheckConstraint, func


class ProductStatus(Enum):
    PENDING   = "PENDING"    # listing newly created by a seller, awaiting admin review
    ACTIVE    = "ACTIVE"     # approved, publicly visible / purchasable
    INACTIVE  = "INACTIVE"   # hidden by the seller (out of stock / supply issue)
    SUSPENDED = "SUSPENDED"  # hidden by an admin due to an issue
    REJECTED  = "REJECTED"   # admin rejected a pending listing (also soft-deleted); terminal


class Product(db.Model):
    """
    Catalog product = the canonical spec/identity of a thing that can be sold
    (brand/name/model/color/size/barcode/specifications). It holds NO price,
    stock, status, or owner — those belong to each seller's `SellerProduct`
    listing. A catalog product is only buyer-visible when it has at least one
    ACTIVE, in-stock listing. See seller_products_design.md.
    """
    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint('brand = TRIM(brand)', name='products_brand_trim_check'),
        CheckConstraint('name = TRIM(name)', name='products_name_trim_check'),
        CheckConstraint('model IS NULL OR model = TRIM(model)', name='products_model_trim_check'),
        CheckConstraint('color IS NULL OR color = TRIM(color)', name='products_color_trim_check'),
        CheckConstraint('size IS NULL OR size = TRIM(size)', name='products_size_trim_check'),
    )

    id          = db.Column(db.Integer, primary_key=True)
    uuid        = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    brand       = db.Column(db.String(100), nullable=False)
    name        = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    model          = db.Column(db.String(255), nullable=True)
    color          = db.Column(db.String(100), nullable=True)
    size           = db.Column(db.String(100), nullable=True)
    # Partial-unique in the DB: unique when NOT NULL (see migration). Null => a
    # new catalog row is always created (dedupe skipped).
    barcode        = db.Column(db.String(50), nullable=True)
    specifications = db.Column(JSONB, nullable=True)
    created_at  = db.Column(db.DateTime(timezone=True), server_default=func.now())
    deleted_at  = db.Column(db.DateTime(timezone=True), nullable=True)

    # Many-to-Many Relationship with Category through category_items helper
    categories = db.relationship('Category', secondary='category_items', backref='products')

    # SellerProduct.catalog defines the reverse `listings` backref.

    def to_dict(self, allowed_fields=None):
        data = {
            'id'            : self.id,
            'uuid'          : self.uuid,
            'brand'         : self.brand,
            'name'          : self.name,
            'description'   : self.description,
            'model'         : self.model,
            'color'         : self.color,
            'size'          : self.size,
            'barcode'       : self.barcode,
            'specifications': self.specifications or {},
            'categories'    : [cat.name for cat in self.categories] if self.categories else [],
            'created_at'    : self.created_at.isoformat() if self.created_at else None,
            'deleted_at'    : self.deleted_at.isoformat() if self.deleted_at else None,
        }
        if allowed_fields:
            return {k: v for k, v in data.items() if k in allowed_fields}
        return data
