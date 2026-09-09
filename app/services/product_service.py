"""
Catalog product service (spec sheet). Admin-curated.

The catalog product holds only shared spec fields (brand/name/model/color/size/
barcode/specifications) + category links. Price/stock/status/owner/images live on
SellerProduct (see seller_product_service.py). Browse/purchasability is driven by
listings, so the public product list here returns catalog rows that have at least
one ACTIVE in-stock listing.
"""
from app.extensions import db
import logging
from sqlalchemy import func
from app.models import Product, SellerProduct, ProductStatus, UserRole
from app.models.category_model import Category
from . import ValidationResponse


def _is_admin(roles):
    return any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)


def _catalog_has_active_listing_subquery():
    """Subquery of product_ids that currently have an ACTIVE, in-stock listing."""
    return (
        db.session.query(SellerProduct.product_id)
        .filter(
            SellerProduct.deleted_at.is_(None),
            SellerProduct.status == ProductStatus.ACTIVE,
            SellerProduct.stock > 0,
        )
    )


def _apply_product_filters(query, filters):
    filters = filters or {}

    search = filters.get("search")
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    category_id = filters.get("category_id")
    if category_id:
        query = query.filter(Product.categories.any(Category.id == category_id))

    category_name = filters.get("category_name")
    if category_name:
        query = query.filter(Product.categories.any(Category.name.ilike(f"%{category_name}%")))

    sort = filters.get("sort")
    sort_columns = {"name": Product.name, "created_at": Product.created_at}
    if sort:
        descending = sort.startswith("-")
        column = sort_columns.get(sort.lstrip("-"))
        if column is not None:
            query = query.order_by(column.desc() if descending else column.asc())
    else:
        query = query.order_by(Product.id.asc())

    return query


def get_all_products(filters=None, jwt_user_id=None, roles=None):
    """
    Catalog list. Non-admin callers only see catalog products that have at least
    one ACTIVE in-stock listing. Admin/superadmin see all non-deleted catalog rows.
    """
    from app.utils.pagination import paginate_query
    roles = roles or []
    try:
        query = Product.query.filter(Product.deleted_at.is_(None))
        if not _is_admin(roles):
            query = query.filter(Product.id.in_(_catalog_has_active_listing_subquery()))
        query = _apply_product_filters(query, filters)
        return paginate_query(query, args=filters)
    except Exception as e:
        logging.error(f"Failed to retrieve products: {str(e)}")
        return None


def get_product_by_id(product_id, jwt_user_id=None, roles=None):
    """Single catalog product. Non-admin: only if it has an ACTIVE listing."""
    roles = roles or []
    try:
        product = Product.query.filter(
            Product.id == product_id,
            Product.deleted_at.is_(None),
        ).first()
        if not product:
            return None

        if _is_admin(roles):
            return product

        has_active = _catalog_has_active_listing_subquery().filter(
            SellerProduct.product_id == product_id
        ).first()
        return product if has_active else None
    except Exception as e:
        logging.error(f"Failed to retrieve product {product_id}: {str(e)}")
        return None


def create_new_product(jwt_user_id, product_instance, client_roles):
    """
    Create a bare catalog product (admin/superadmin only). Sellers create
    catalog implicitly through the seller-products endpoint (Option B).
    `product_instance` is a Product model built by ProductSchema(load_instance).
    """
    from flask import request
    if not _is_admin(client_roles):
        return ValidationResponse(success=False, message="Only admin/superadmin can create catalog products directly")

    raw = request.get_json(silent=True) or {}
    category_ids = raw.get("category_ids", [])
    if category_ids:
        categories = Category.query.filter(Category.id.in_(category_ids)).all()
        if len(categories) != len(category_ids):
            return ValidationResponse(success=False, message="Some category IDs not found")
        product_instance.categories = categories
    else:
        product_instance.categories = []

    try:
        db.session.add(product_instance)
        db.session.commit()
        logging.info(f"Catalog product created: {product_instance.id}")
        return product_instance
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create catalog product: {str(e)}")
        return None


def update_product(product_id, update_data, jwt_user_id, roles):
    """Update catalog spec fields (admin/superadmin only)."""
    from app.permissions.field_filter import get_allowed_fields
    try:
        product = Product.query.filter(
            Product.id == product_id,
            Product.deleted_at.is_(None),
        ).first()
        if not product:
            return ValidationResponse(success=False, message="Product not found")

        if not _is_admin(roles):
            return ValidationResponse(success=False, message="Only admin/superadmin can update catalog products")

        allowed = get_allowed_fields("products", roles, "update")

        category_ids = update_data.pop("category_ids", None)
        if category_ids is not None and "category_ids" in allowed:
            categories = Category.query.filter(Category.id.in_(category_ids)).all()
            if len(categories) != len(category_ids):
                return ValidationResponse(success=False, message="Some category IDs not found")
            product.categories = categories

        for key, value in update_data.items():
            if key in allowed and hasattr(product, key):
                setattr(product, key, value)

        db.session.commit()
        logging.info(f"Catalog product updated: {product.id}")
        return product
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update product: {str(e)}")
        return None


def delete_product(product_id, jwt_user_id, roles, action="soft"):
    """
    Delete a catalog product (admin soft / superadmin hard). Blocked if any of
    its listings is linked to an active PAID order.
    """
    from app.permissions.field_filter import get_delete_policy
    from app.models.order_model import Order, OrderStatus
    from app.models.order_items_model import Order_item
    try:
        product = Product.query.filter(Product.id == product_id).first()
        if not product:
            return ValidationResponse(success=False, message="Product not found", status_code=404)

        delete_policy = get_delete_policy("products", roles)
        if delete_policy is None:
            return ValidationResponse(success=False, message="Your role does not have permission to delete products", status_code=403)

        # Guard: any listing of this catalog product tied to a PAID order.
        active_order_count = (
            Order_item.query
            .join(Order, Order_item.order_id == Order.id)
            .join(SellerProduct, Order_item.seller_product_id == SellerProduct.id)
            .filter(
                SellerProduct.product_id == product_id,
                Order.status == OrderStatus.PAID,
                Order.deleted_at.is_(None),
            ).count()
        )
        if active_order_count > 0:
            return ValidationResponse(
                success=False,
                message=f"Unable to delete this product. It has listings linked to {active_order_count} active order(s).",
                status_code=409,
            )

        if action == "hard":
            if delete_policy != "hard":
                return ValidationResponse(success=False, message="Only superadmin can perform hard delete", status_code=403)
            db.session.delete(product)  # cascades to seller_products + order_items
            db.session.commit()
            logging.info(f"Catalog product hard-deleted: {product_id}")
            return ValidationResponse(success=True, message=f"Product {product_id} permanently deleted", status_code=200)

        if product.deleted_at is not None:
            return ValidationResponse(success=False, message="Product is already deleted", status_code=400)
        product.deleted_at = func.now()
        db.session.commit()
        logging.info(f"Catalog product soft-deleted: {product_id}")
        return ValidationResponse(success=True, message=f"Product {product_id} soft-deleted", status_code=200)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete product {product_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while deleting the product.", status_code=500)
