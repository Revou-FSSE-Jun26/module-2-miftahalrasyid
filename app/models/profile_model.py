from app.extensions import db
from sqlalchemy import func


class Profile(db.Model):
    __tablename__ = 'profiles'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    bio        = db.Column(db.String(500), nullable=True)
    avatar_url = db.Column(db.String(300), nullable=True)
    phone      = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship('User', backref=db.backref('profile', uselist=False, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
