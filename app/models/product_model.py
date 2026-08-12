from app import db
import datetime as dt
from sqlalchemy import CheckConstraint

class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='products_quantity_check'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    brand = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))

    # Many-to-Many Relationship with Category through category_items helper
    categories = db.relationship('Category', secondary='category_items', backref='products')
    
    seller = db.relationship('User', backref='products')
