from app.extensions import db
from sqlalchemy import func

category_items = db.Table(
    'category_items',
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime(timezone=True), server_default=func.now())
)
