from app import db
import datetime as dt
from sqlalchemy import CheckConstraint

class Category(db.Model):
    __tablename__ = 'categories'
    __table_args__ = (
        CheckConstraint('lower(name) = name', name='categories_name_check'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))
