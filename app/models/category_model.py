from app.extensions import db
import datetime as dt
from sqlalchemy import CheckConstraint, func

class Category(db.Model):
    __tablename__ = 'categories'
    __table_args__ = (
        CheckConstraint('lower(name) = name', name='categories_name_check'),
    )

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), unique=True, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self, allowed_fields=None):
        data = {
            "id"        : self.id,
            "name"      : self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        if allowed_fields:
            return {k: v for k, v in data.items() if k in allowed_fields}
        return data
