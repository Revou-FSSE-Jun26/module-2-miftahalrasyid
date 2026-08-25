from app.extensions import db
import logging
from sqlalchemy import func
from app.models.profile_model import Profile
from . import ValidationResponse


def get_profile_by_user_id(user_id):
    """Get a user's profile."""
    try:
        return Profile.query.filter_by(user_id=user_id).first()
    except Exception as e:
        logging.error(f"Failed to retrieve profile for user {user_id}: {str(e)}")
        return None


def create_profile(user_id):
    """Create an empty profile for a user (called during registration)."""
    try:
        existing = Profile.query.filter_by(user_id=user_id).first()
        if existing:
            return existing

        profile = Profile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
        return profile
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create profile for user {user_id}: {str(e)}")
        return None


def update_profile(user_id, update_data):
    """Update a user's profile fields."""
    try:
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            return ValidationResponse(success=False, message="Profile not found")

        for key, value in update_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = func.now()
        db.session.commit()
        return profile
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update profile for user {user_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while updating profile.")
