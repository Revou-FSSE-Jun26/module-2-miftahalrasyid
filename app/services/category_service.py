from app.extensions import db
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.models import Category, UserRole
from . import ValidationResponse


def get_all_categories():
    """
    Get all active categories with pagination.
    Reads ?page and ?per_page from query params.
    """
    from app.utils.pagination import paginate_query
    try:
        query = Category.query.filter(Category.deleted_at.is_(None))
        return paginate_query(query)
    except Exception as e:
        logging.error(f"Failed to retrieve categories: {str(e)}")
        return None


def get_category_by_id(category_id):
    """
    Get a single category by ID (must not be soft-deleted).
    """
    try:
        return Category.query.filter(
            Category.id == category_id,
            Category.deleted_at.is_(None)
        ).first()
    except Exception as e:
        logging.error(f"Failed to retrieve category {category_id}: {str(e)}")
        return None


def create_category(category_instance, roles):
    """
    Create a new category. Only admin/superadmin allowed.
    
    Args:
        category_instance: Category model instance from Marshmallow schema
        roles: User's roles from JWT
    
    Returns:
        Category on success, ValidationResponse on error, None on failure
    """
    from app.permissions.field_filter import get_allowed_fields

    # RBAC: check create permission
    allowed = get_allowed_fields("categories", roles, "create")
    if not allowed:
        return ValidationResponse(success=False, message="Your role does not have permission to create categories")

    try:
        db.session.add(category_instance)
        db.session.commit()
        logging.info(f"Category created successfully: {category_instance.id}")
        return category_instance
    except IntegrityError as e:
        db.session.rollback()
        error_msg = str(e.orig) if e.orig else str(e)
        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            return ValidationResponse(success=False, message="Category name already exists")
        logging.error(f"Integrity error creating category: {error_msg}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create category: {str(e)}")
        return None


def update_category(category_id, update_data, roles):
    """
    Update a category by ID with RBAC field-level filtering.
    
    Args:
        category_id: Category ID to update
        update_data: Dict of fields to update
        roles: User's roles from JWT
    
    Returns:
        Category on success, ValidationResponse on error, None on failure
    """
    from app.permissions.field_filter import get_allowed_fields

    try:
        category = Category.query.filter(
            Category.id == category_id,
            Category.deleted_at.is_(None)
        ).first()

        if not category:
            return ValidationResponse(success=False, message="Category not found")

        # RBAC: filter fields by role
        allowed = get_allowed_fields("categories", roles, "update")
        if not allowed:
            return ValidationResponse(success=False, message="Your role does not have permission to update categories")

        blocked_fields = set(update_data.keys()) - allowed
        if blocked_fields and not (set(update_data.keys()) & allowed):
            return ValidationResponse(
                success=False,
                message=f"Your role does not have permission to update: {', '.join(blocked_fields)}"
            )

        # Update only allowed scalar fields
        for key, value in update_data.items():
            if key in allowed and hasattr(category, key):
                setattr(category, key, value)

        db.session.commit()
        logging.info(f"Category updated successfully: {category.id}")
        return category

    except IntegrityError as e:
        db.session.rollback()
        error_msg = str(e.orig) if e.orig else str(e)
        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            return ValidationResponse(success=False, message="Category name already exists")
        logging.error(f"Integrity error updating category: {error_msg}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update category: {str(e)}")
        return None


def delete_category(category_id, roles, action="soft"):
    """
    Delete a category by ID.
    Default = soft delete (set deleted_at).
    Superadmin can pass action="hard" to permanently remove.
    
    Args:
        category_id: Category ID to delete
        roles: User's roles from JWT
        action: "soft" (default) or "hard" (superadmin only)
    
    Returns:
        dict on success, ValidationResponse on error, None on failure
    """
    from app.permissions.field_filter import get_delete_policy

    try:
        category = Category.query.filter(Category.id == category_id).first()

        if not category:
            return ValidationResponse(success=False, message="Category not found", status_code=404)

        # Check delete permission
        delete_policy = get_delete_policy("categories", roles)
        if delete_policy is None:
            return ValidationResponse(success=False, message="Your role does not have permission to delete categories", status_code=403)

        # Hard delete: only if role policy allows "hard" AND action requested is "hard"
        if action == "hard":
            if delete_policy != "hard":
                return ValidationResponse(success=False, message="Only superadmin can perform hard delete", status_code=403)
            db.session.delete(category)
            db.session.commit()
            logging.info(f"Category hard-deleted: {category_id}")
            return ValidationResponse(success=True, message=f"Category {category_id} permanently deleted", status_code=200)

        # Soft delete (default)
        if category.deleted_at is not None:
            return ValidationResponse(success=False, message="Category is already deleted", status_code=400)
        category.deleted_at = func.now()
        db.session.commit()
        logging.info(f"Category soft-deleted: {category_id}")
        return ValidationResponse(success=True, message=f"Category {category_id} soft-deleted", status_code=200)

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Integrity error deleting category {category_id}: {str(e)}")
        return ValidationResponse(success=False, message="Cannot delete this category due to database integrity constraints.", status_code=409)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete category {category_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while deleting the category.", status_code=500)
