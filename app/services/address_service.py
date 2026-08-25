from app.extensions import db
import logging
from app.models.address_model import Address
from . import ValidationResponse


MAX_ADDRESSES_PER_USER = 5


def get_addresses_by_user(user_id):
    """Get all addresses for a user."""
    try:
        return Address.query.filter_by(user_id=user_id).all()
    except Exception as e:
        logging.error(f"Failed to retrieve addresses for user {user_id}: {str(e)}")
        return None


def get_address_by_id(address_id, user_id):
    """Get a single address by ID, scoped to user."""
    try:
        return Address.query.filter_by(id=address_id, user_id=user_id).first()
    except Exception as e:
        logging.error(f"Failed to retrieve address {address_id}: {str(e)}")
        return None


def create_address(user_id, address_instance):
    """
    Create a new address for a user.
    If is_default=True, unset other defaults first.
    Max 5 addresses per user.
    """
    try:
        # Check limit
        count = Address.query.filter_by(user_id=user_id).count()
        if count >= MAX_ADDRESSES_PER_USER:
            return ValidationResponse(success=False, message=f"Maximum {MAX_ADDRESSES_PER_USER} addresses allowed per account")

        address_instance.user_id = user_id

        # If this is set as default, unset others
        if address_instance.is_default:
            Address.query.filter_by(user_id=user_id, is_default=True).update({"is_default": False})

        # If this is the first address, make it default
        if count == 0:
            address_instance.is_default = True

        db.session.add(address_instance)
        db.session.commit()
        return address_instance
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create address for user {user_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while creating address.")


def update_address(address_id, user_id, update_data):
    """Update an existing address."""
    try:
        address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        if not address:
            return ValidationResponse(success=False, message="Address not found")

        # If setting as default, unset others first
        if update_data.get("is_default") is True:
            Address.query.filter_by(user_id=user_id, is_default=True).update({"is_default": False})

        for key, value in update_data.items():
            if hasattr(address, key):
                setattr(address, key, value)

        db.session.commit()
        return address
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update address {address_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while updating address.")


def delete_address(address_id, user_id):
    """Delete an address. If it was default, promote another."""
    try:
        address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        if not address:
            return ValidationResponse(success=False, message="Address not found")

        was_default = address.is_default
        db.session.delete(address)
        db.session.commit()

        # If deleted address was default, promote the first remaining one
        if was_default:
            remaining = Address.query.filter_by(user_id=user_id).first()
            if remaining:
                remaining.is_default = True
                db.session.commit()

        return ValidationResponse(success=True, message="Address deleted successfully", status_code=200)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete address {address_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while deleting address.")
