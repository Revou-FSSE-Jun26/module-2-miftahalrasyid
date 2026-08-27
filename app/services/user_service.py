from app.extensions import db
from dataclasses import dataclass
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.models.user_model import User, UserRole, AuthProvider
import logging
import hashlib
from email_validator import validate_email, EmailNotValidError
from . import ValidationResponse


def get_all_users():
    """
    Retrieve all users with pagination.
    Reads ?page and ?per_page from query params.
    """
    from app.utils.pagination import paginate_query
    try:
        query = User.query.filter(User.deleted_at.is_(None))
        return paginate_query(query)
    except Exception as e:
        logging.error(f"Failed to retrieve users: {str(e)}")
        return None


def get_user_by(id):
    """
    Retrieve a single user by ID.
    Includes error handling for database connection issues.
    """
    try:
        user = db.session.query(User).get(id)
        return user
    except Exception as e:
        logging.error(f"Failed to retrieve user ID {id}: {str(e)}")
        return None


def get_user_detail(user_id):
    """
    Retrieve a user by ID with their profile and addresses.
    Used by admin to view full user details.
    
    Returns:
        dict with user, profile, addresses on success. None if not found.
    """
    from app.services.profile_service import get_profile_by_user_id
    from app.services.address_service import get_addresses_by_user

    try:
        user = db.session.query(User).get(user_id)
        if not user:
            return None

        profile = get_profile_by_user_id(user_id)
        addresses = get_addresses_by_user(user_id)

        data = user.to_dict()
        data["profile"] = profile.to_dict() if profile else None
        data["addresses"] = [addr.to_dict() for addr in addresses] if addresses else []

        return data
    except Exception as e:
        logging.error(f"Failed to retrieve user detail for ID {user_id}: {str(e)}")
        return None


def delete_user(user_id, caller_roles, action="soft"):
    """
    Delete a user by ID.
    Default = soft delete (set deleted_at).
    Superadmin can pass action="hard" to permanently remove.
    
    Args:
        user_id: User ID to delete
        caller_roles: Caller's roles from JWT
        action: "soft" (default) or "hard" (superadmin only)
    
    Returns:
        dict on success, ValidationResponse on error, None on failure
    """
    from app.permissions.field_filter import get_delete_policy

    try:
        user = User.query.get(user_id)
        if user is None:
            return ValidationResponse(success=False, message="User not found.", status_code=404)

        delete_policy = get_delete_policy("users", caller_roles)
        if delete_policy is None:
            return ValidationResponse(success=False, message="Your role does not have permission to delete users.", status_code=403)

        # Block deletion of sellers who have active PAID orders (via their products)
        if user.roles and UserRole.SELLER in user.roles:
            from app.models.order_model import Order, OrderStatus
            from app.models.order_items_model import Order_item
            from app.models.product_model import Product
            active_paid_orders = Order_item.query.join(
                Product, Order_item.product_id == Product.id
            ).join(
                Order, Order_item.order_id == Order.id
            ).filter(
                Product.user_id == user_id,
                Order.status == OrderStatus.PAID,
                Order.deleted_at.is_(None)
            ).count()
            if active_paid_orders > 0:
                return ValidationResponse(
                    success=False,
                    message=f"Cannot delete this seller. They have {active_paid_orders} active order(s) with PAID status. Please complete or cancel those orders first.",
                    status_code=409
                )

        # Hard delete: only if role policy allows "hard" AND action requested is "hard"
        if action == "hard":
            if delete_policy != "hard":
                return ValidationResponse(success=False, message="Only superadmin can perform hard delete", status_code=403)
            db.session.delete(user)
            db.session.commit()
            logging.info(f"User hard-deleted: {user_id}")
            return ValidationResponse(success=True, message=f"User {user_id} permanently deleted", status_code=200)

        # Soft delete (default)
        if user.deleted_at is not None:
            return ValidationResponse(success=False, message="This user account is already deactivated.", status_code=400)
        user.deleted_at = func.now()
        db.session.commit()
        logging.info(f"User soft-deleted: {user_id}")
        return ValidationResponse(success=True, message=f"User {user_id} soft-deleted", status_code=200)

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Integrity error deleting user {user_id}: {str(e)}")
        return ValidationResponse(success=False, message="Cannot delete this user due to database integrity constraints.", status_code=409)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete user {user_id}: {str(e)}")
        return ValidationResponse(success=False, message="Unexpected error during delete.", status_code=500)


def update_user_by(id, user_instance, caller_roles=None):
    """
    Update user fields by ID with RBAC field-level filtering.
    Only fields allowed by the caller's role will be applied.
    Blocks OAuth users from updating password.
    """
    from app.permissions.field_filter import get_allowed_fields

    if caller_roles is None:
        caller_roles = []

    try:
        user = User.query.get(id)
        if user is None:
            return ValidationResponse(success=False, message="User not found.")

        # Get allowed fields for this role
        allowed = get_allowed_fields("users", caller_roles, "update")

        # Block OAuth users from updating password
        if user.provider != AuthProvider.PASSWORD_HASH:
            if "password" in allowed:
                allowed = allowed - {"password"}

        # Apply age if allowed
        if "age" in allowed:
            age_val = getattr(user_instance, 'age', None)
            if age_val is not None and age_val != "":
                user.age = age_val

        # Apply password if allowed
        if "password" in allowed:
            new_hash_password = getattr(user_instance, 'provider_key', None)
            if new_hash_password is not None and new_hash_password != "":
                user.provider_key = new_hash_password

        # Apply roles if allowed (admin/superadmin only)
        if "roles" in allowed:
            roles_val = getattr(user_instance, 'roles', None)
            if roles_val is not None:
                # Convert string list to UserRole enum list
                user.roles = [UserRole(r) for r in roles_val]

        # Apply is_active if allowed (admin/superadmin only)
        if "is_active" in allowed:
            is_active_val = getattr(user_instance, 'is_active', None)
            if is_active_val is not None:
                user.is_active = is_active_val

        # Check if any field was actually in the allowed set
        attempted_fields = set()
        if getattr(user_instance, 'age', None) is not None:
            attempted_fields.add("age")
        if getattr(user_instance, 'provider_key', None) is not None:
            attempted_fields.add("password")
        if getattr(user_instance, 'roles', None) is not None:
            attempted_fields.add("roles")
        if getattr(user_instance, 'is_active', None) is not None:
            attempted_fields.add("is_active")

        blocked_fields = attempted_fields - allowed
        if blocked_fields and not (attempted_fields & allowed):
            return ValidationResponse(
                success=False,
                message=f"Your role does not have permission to update: {', '.join(blocked_fields)}"
            )

        db.session.commit()
        return user
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error during update on id:{id}: {str(e)}")
        return ValidationResponse(success=False, message=f"Unexpected error during update on id:{id}")


def become_seller(user_id):
    """
    Add SELLER role to user's role array if not already present.
    """
    try:
        user = User.query.get(user_id)
        if user is None:
            return ValidationResponse(success=False, message="User not found.")

        if user.deleted_at is not None:
            return ValidationResponse(success=False, message="This account has been deactivated.")

        if UserRole.SELLER in (user.roles or []):
            return ValidationResponse(success=False, message="You are already a seller.")

        # Add SELLER to existing roles
        current_roles = list(user.roles) if user.roles else []
        current_roles.append(UserRole.SELLER)
        user.roles = current_roles
        db.session.commit()

        return user
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error during become_seller for id:{user_id}: {str(e)}")
        return ValidationResponse(success=False, message="Unexpected error during role update.")


def add_new_users(user_instance):
    """
    Add a new user to the database.
    Accepts 'user_instance' as a full SQLAlchemy User Model object from Smorest.
    """
    # 1. Extract raw data from the object properties sent by Smorest
    email = user_instance.email

    # 2. Run email normalization & validation
    validated_email = normalize_and_validate_email(email)
    if validated_email is None:
        return ValidationResponse(success=False, message="Email format is wrong")

    try:
        # 3. Generate internal system data automatically
        username = validated_email.split('@')[0]

        user_instance.username = username
        user_instance.email = validated_email

        db.session.add(user_instance)
        db.session.commit()

        return user_instance

    except IntegrityError as e:
        db.session.rollback()

        error_msg = str(e.orig)

        if "users_email_key" in error_msg or "already exists" in error_msg:
            return ValidationResponse(success=False, message=f"Email '{validated_email}' is already registered.")

        return ValidationResponse(success=False, message="Database integrity constraint violation.")

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to process user registration: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected database error occurred.")


def normalize_and_validate_email(email_input):
    """
    Normalize email to prevent alias manipulation (especially Gmail).
    Example: 'andrew.twitter+youtube@gmail.com' -> 'andrew@gmail.com'
    """
    if not email_input or not isinstance(email_input, str):
        return None

    email_address = email_input.strip().lower()
    if '@' not in email_address:
        return None

    username_part, domain_part = email_address.split('@', 1)

    # Gmail-specific normalization
    if domain_part in ['gmail.com', 'googlemail.com']:
        username_part = username_part.split('+')[0]   # Remove everything after +
        username_part = username_part.replace('.', '')  # Remove all dots

    cleaned_email = f"{username_part}@{domain_part}"

    try:
        email_info = validate_email(cleaned_email, check_deliverability=True)
        return email_info.normalized

    except EmailNotValidError as e:
        logging.warning(f"Email failed internet validation: {cleaned_email}. Reason: {str(e)}")
        return None
