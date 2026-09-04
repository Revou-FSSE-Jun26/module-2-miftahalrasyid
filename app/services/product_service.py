from app.extensions import db
import logging
import os
import re
from flask import request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.models import Product,UserRole
from app.models.category_model import Category
from . import ValidationResponse


def generate_slug(name):
    """
    Generate a unique slug from product name.
    Converts to lowercase, replaces spaces/special chars with hyphens,
    appends a number suffix if the slug already exists.
    """
    # Lowercase, replace non-alphanumeric with hyphens, collapse multiple hyphens
    base_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    base_slug = re.sub(r'-+', '-', base_slug)

    slug = base_slug
    counter = 1
    while Product.query.filter_by(slug=slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

    
def _apply_product_filters(query, filters):
    """
    Apply search / category / price filters and sorting to a Product query.
    `filters` is the validated query-args dict (all keys optional).
    """
    filters = filters or {}

    search = filters.get("search")
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    category_id = filters.get("category_id")
    if category_id:
        query = query.filter(Product.categories.any(Category.id == category_id))

    category_name = filters.get("category_name")
    if category_name:
        # Partial, case-insensitive match on category name. Unknown names simply
        # yield no matching products (empty result, not a 404).
        query = query.filter(Product.categories.any(Category.name.ilike(f"%{category_name}%")))

    min_price = filters.get("min_price")
    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    max_price = filters.get("max_price")
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    sort = filters.get("sort")
    sort_columns = {"price": Product.price, "name": Product.name, "created_at": Product.created_at}
    if sort:
        descending = sort.startswith("-")
        column = sort_columns.get(sort.lstrip("-"))
        if column is not None:
            query = query.order_by(column.desc() if descending else column.asc())
    else:
        query = query.order_by(Product.id.asc())

    return query


def get_all_products(filters=None):
    """
    Get all active products with pagination, filtering and sorting.

    Args:
        filters: validated query-args dict (page, per_page, search,
                 category_id, min_price, max_price, sort). All optional.
    """
    from app.utils.pagination import paginate_query
    try:
        query = Product.query.filter(Product.deleted_at.is_(None)).filter_by(is_active=True)
        query = _apply_product_filters(query, filters)
        return paginate_query(query, args=filters)
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
    For admin/superadmin: use the client-provided user_id (create on behalf of others).
    For seller: always use jwt_user_id (own products only).
    """
    if any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles):
        # Admin can specify user_id; fall back to jwt_user_id if not provided or invalid
        if client_user_id and isinstance(client_user_id, int):
            return client_user_id
        return int(jwt_user_id)
    else:
        return int(jwt_user_id)

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
        # Auto-generate slug from product name if not already set
        if not product_instance.slug:
            product_instance.slug = generate_slug(product_instance.name)

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
    Update a product by ID with RBAC field-level filtering.
    Only owner, admin, or superadmin can update.
    
    Args:
        product_id: Product ID to update
        update_data: Dict of fields to update
        jwt_user_id: Authenticated user's ID
        roles: User's roles from JWT
    
    Returns:
        Product on success, ValidationResponse on error, None on failure
    """
    from app.permissions.field_filter import get_allowed_fields

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

        # RBAC: filter fields by role
        allowed = get_allowed_fields("products", roles, "update")
        blocked_fields = set(update_data.keys()) - allowed - {"category_ids"}
        if blocked_fields and not (set(update_data.keys()) & allowed):
            return ValidationResponse(
                success=False,
                message=f"Your role does not have permission to update: {', '.join(blocked_fields)}"
            )

        # Handle category_ids separately (if allowed)
        category_ids = update_data.pop('category_ids', None)
        if category_ids is not None and "category_ids" in allowed:
            categories = Category.query.filter(Category.id.in_(category_ids)).all()
            if len(categories) != len(category_ids):
                return ValidationResponse(success=False, message="Some category IDs not found")
            product.categories = categories

        # Update only allowed scalar fields
        for key, value in update_data.items():
            if key in allowed and hasattr(product, key):
                setattr(product, key, value)

        # Regenerate slug if name was updated
        if "name" in update_data and "name" in allowed:
            product.slug = generate_slug(product.name)

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


def delete_product(product_id, jwt_user_id, roles, action="soft"):
    """
    Delete a product by ID.
    Default = soft delete (set deleted_at).
    Superadmin can pass action="hard" to permanently remove.
    Blocks deletion if product is linked to active (PAID) orders.
    
    Args:
        product_id: Product ID to delete
        jwt_user_id: Authenticated user's ID
        roles: User's roles from JWT
        action: "soft" (default) or "hard" (superadmin only)
    
    Returns:
        dict on success, ValidationResponse on error, None on failure
    """
    from app.permissions.field_filter import get_delete_policy

    try:
        product = Product.query.filter(Product.id == product_id).first()

        if not product:
            return ValidationResponse(success=False, message="Product not found", status_code=404)

        # Check delete permission
        delete_policy = get_delete_policy("products", roles)
        if delete_policy is None:
            return ValidationResponse(success=False, message="Your role does not have permission to delete products", status_code=403)

        # Authorization: owner or admin/superadmin
        is_admin = any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)
        if product.user_id != int(jwt_user_id) and not is_admin:
            return ValidationResponse(success=False, message="Unauthorized to delete this product", status_code=403)

        # Block deletion if product is linked to active (PAID) orders
        from app.models.order_model import Order, OrderStatus
        from app.models.order_items_model import Order_item
        active_order_count = Order_item.query.join(
            Order, Order_item.order_id == Order.id
        ).filter(
            Order_item.product_id == product_id,
            Order.status == OrderStatus.PAID,
            Order.deleted_at.is_(None)
        ).count()
        if active_order_count > 0:
            return ValidationResponse(
                success=False,
                message=f"Unable to delete this product. It is linked to {active_order_count} active order(s) awaiting fulfillment. Please complete or cancel those orders first.",
                status_code=409
            )

        # Hard delete: only if role policy allows "hard" AND action requested is "hard"
        if action == "hard":
            if delete_policy != "hard":
                return ValidationResponse(success=False, message="Only superadmin can perform hard delete", status_code=403)
            # Clean up uploaded images from filesystem
            import shutil
            uploads_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')
            product_folder = os.path.join(uploads_root, 'products', product.uuid)
            if os.path.isdir(product_folder):
                shutil.rmtree(product_folder)
                logging.info(f"Deleted image folder for product {product_id}: {product_folder}")
            db.session.delete(product)
            db.session.commit()
            logging.info(f"Product hard-deleted: {product_id}")
            return ValidationResponse(success=True, message=f"Product {product_id} permanently deleted", status_code=200)

        # Soft delete (default)
        if product.deleted_at is not None:
            return ValidationResponse(success=False, message="Product is already deleted", status_code=400)
        # Remove images from filesystem and nullify in DB
        import shutil
        uploads_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')
        product_folder = os.path.join(uploads_root, 'products', product.uuid)
        if os.path.isdir(product_folder):
            shutil.rmtree(product_folder)
            logging.info(f"Deleted image folder for product {product_id}: {product_folder}")
        product.images = None
        product.deleted_at = func.now()
        db.session.commit()
        logging.info(f"Product soft-deleted: {product_id}")
        return ValidationResponse(success=True, message=f"Product {product_id} soft-deleted", status_code=200)

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Integrity error deleting product {product_id}: {str(e)}")
        return ValidationResponse(success=False, message="Cannot delete this product due to database integrity constraints. It may still be referenced by other records.", status_code=409)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete product {product_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while deleting the product.", status_code=500)