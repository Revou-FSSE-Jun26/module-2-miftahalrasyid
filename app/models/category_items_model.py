from app import db
import datetime as dt

category_items = db.Table(
    'category_items',
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))
)
