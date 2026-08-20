from app.extensions import db
import logging
from flask import request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.models import Product,UserRole
from app.models.category_model import Category
from . import ValidationResponse

    
def get_all_products():
    """
        Get all active products for buyer to browse (deleted_at is null and is_active is true)
    """
    try:
        query = Product.query.filter(Product.deleted_at.is_(None)).filter_by(is_active=True)
        pagination = query.paginate(page=1, per_page=10, max_per_page=20, error_out=True, count=True)
        return [product.to_dict() for product in pagination.items]
    except Exception as e:
        logging.error(f"Failed to retrieve products: {str(e)}")
        return None


def get_product_by_id(product_id):
    """
    Get a single product by ID (must not be soft-deleted).
    Returns Product instance or None.
    """
    try:
        return Product.query.filter(
            Product.id == product_id,
            Product.deleted_at.is_(None)
        ).first()
    except Exception as e:
        logging.error(f"Failed to retrieve product {product_id}: {str(e)}")
        return None

def validate_authorization(client_user_id,jwt_user_id,roles):
    """
    add jwt user_id to mock api for admin and superadmin level
    """
    if not any(r in (UserRole.ADMIN.value,UserRole.SUPERADMIN.value) for r in roles):
        return client_user_id
    else:
        return jwt_user_id

def create_new_product(jwt_user_id, product_instance,client_roles):
    """
    Create a new product with optional fields (stock, sku, categories).
    
    Args:
        user_id: The seller's user ID
        product_instance: Product model instance from Marshmallow schema (already validated)
        Categories should already be set on the instance by the route handler
    
    Returns:
        Product instance on success, None on failure
    """
    
    # check the role
    product_instance.user_id = validate_authorization(
        product_instance.user_id,
        jwt_user_id,client_roles
    )
    
    # Get category IDs from the raw request body
    # (the schema's pre_load removed them before model instantiation)
    raw_data = request.get_json(silent=True) or {}
    category_ids = raw_data.get('category_ids', [])
    
    # Fetch Category objects from database using the IDs
    if category_ids:
        categories = Category.query.filter(Category.id.in_(category_ids)).all()
        
        # Validate all category IDs exist
        if len(categories) != len(category_ids):
            return ValidationResponse(success=False,message="Some category IDs not found")
        
        product_instance.categories = categories
    else:
        product_instance.categories = []
    try:
        # product_instance already has all fields set by the route handler
        # Just save it to the database
        db.session.add(product_instance)
        db.session.commit()
        
        logging.info(f"Product created successfully: {product_instance.id}")
        return product_instance
        
    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Database integrity error creating product: {str(e)}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create product: {str(e)}")
        return None
    
def update_product(product_id, update_data, jwt_user_id, roles):
    """
    Update a product by ID. Only owner, admin, or superadmin can update.
    
    Args:
        product_id: Product ID to update
        update_data: Dict of fields to update
        jwt_user_id: Authenticated user's ID
        roles: User's roles from JWT
    
    Returns:
        Product on success, ValidationResponse on error, None on failure
    """
    try:
        product = Product.query.filter(
            Product.id == product_id,
            Product.deleted_at.is_(None)
        ).first()

        if not product:
            return ValidationResponse(success=False, message="Product not found")

        # Authorization: owner or admin/superadmin
        is_admin = any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)
        if product.user_id != int(jwt_user_id) and not is_admin:
            return ValidationResponse(success=False, message="Unauthorized to update this product")

        # Handle category_ids separately
        category_ids = update_data.pop('category_ids', None)
        if category_ids is not None:
            categories = Category.query.filter(Category.id.in_(category_ids)).all()
            if len(categories) != len(category_ids):
                return ValidationResponse(success=False, message="Some category IDs not found")
            product.categories = categories

        # Update scalar fields
        for key, value in update_data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        db.session.commit()
        logging.info(f"Product updated successfully: {product.id}")
        return product

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Integrity error updating product: {str(e)}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update product: {str(e)}")
        return None


def get_products_by_user(id):
    """
        get all products only for the product owner with deleted_at null
    """
    