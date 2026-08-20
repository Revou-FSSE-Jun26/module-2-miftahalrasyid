from app.extensions import db
import datetime as dt
from sqlalchemy import CheckConstraint,func

class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint('stock >= 0', name='products_stock_check'),
    )

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name        = db.Column(db.String(150), nullable=False)
    stock       = db.Column(db.Integer, default=0)
    brand       = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    price       = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at  = db.Column(db.DateTime(timezone=True),server_default=func.now())
    is_active   = db.Column(db.Boolean,default=True)
    sku         = db.Column(db.String(50),nullable=True)
    deleted_at  = db.Column(db.DateTime(timezone=True),nullable=True)
    # Many-to-Many Relationship with Category through category_items helper
    categories = db.relationship('Category', secondary='category_items', backref='products')
    
    seller = db.relationship('User', backref='products')
    
    def to_dict(self):
        return {
            'id'         : self.id,
            'user_id'       : self.user_id,
            'name'       : self.name,
            'sku'        : self.sku,
            'brand'       : self.brand,
            'description': self.description,
            'price'      : float(self.price),
            'stock'      : self.stock,
            'is_active'  : self.is_active,
            'categories' : [cat.name for cat in self.categories] if self.categories else [],
            'created_at' : self.created_at.isoformat() if self.created_at else None,
            'deleted_at' : self.deleted_at.isoformat() if self.deleted_at else None,
        }
