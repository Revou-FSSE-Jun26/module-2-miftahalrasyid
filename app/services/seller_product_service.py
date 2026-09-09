"""
Seller-product (listing) service.

A `SellerProduct` is one seller's offer for a catalog `Product`. This module owns:
  - browse_listings()   : storefront window query (every active offer + min_price)
  - get_my_listings()   : a seller's own listings (any status)
  - get_listing_by_id() : single listing (visibility-aware)
  - create_listing()    : Option B — find-or-create catalog + create PENDING listing
  - update_listing()    : seller edits own; admin approve/suspend/reject (status matrix)
  - delete_listing()    : soft (default) / hard (superadmin), PAID-order guard

See seller_products_design.md.
"""
from app.extensions import db
import logging
import os
import re
from flask import request
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.models import (
    Product, SellerProduct, ProductStatus, UserRole,
)
from app.models.category_model import Category
from . import ValidationResponse


# =============================================================================
# STATUS TRANSITION MATRIX (moved from product_service; retargeted to listings)
# =============================================================================
_SELLER_TRANSITIONS = {
    ProductStatus.ACTIVE:   {ProductStatus.INACTIVE},
    ProductStatus.INACTIVE: {ProductStatus.ACTIVE},
}
_ADMIN_TRANSITIONS = {
    ProductStatus.PENDING:   {ProductStatus.ACTIVE, ProductStatus.REJECTED},
    ProductStatus.ACTIVE:    {ProductStatus.INACTIVE, ProductStatus.SUSPENDED},
    ProductStatus.INACTIVE:  {ProductStatus.ACTIVE},
    ProductStatus.SUSPENDED: {ProductStatus.ACTIVE},
    # REJECTED is terminal.
}


def is_transition_allowed(current, new_status, is_admin):
    if current == new_status:
        return True
    table = _ADMIN_TRANSITIONS if is_admin else _SELLER_TRANSITIONS
    return new_status in table.get(current, set())


def _is_admin(roles):
    return any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)


def generate_listing_slug(title):
    """Unique slug from a listing title (collision suffix on seller_products.slug)."""
    base = re.sub(r'[^a-z0-9]+', '-', (title or '').lower()).strip('-')
    base = re.sub(r'-+', '-', base) or 'listing'
    slug = base
    counter = 1
    while SellerProduct.query.filter_by(slug=slug).first() is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


# =============================================================================
# BROWSE (storefront) — window query, every active offer tagged with min_price
# =============================================================================

def browse_listings(filters=None, roles=None):
    """
    Public storefront browse. Returns every ACTIVE, in-stock listing whose
    catalog product is not deleted, each row annotated with the per-product
    `min_price`. Pagination preserved via the shared paginate_query helper.
    """
    from app.utils.pagination import paginate_query
    from app.permissions.field_filter import get_allowed_fields

    filters = filters or {}
    roles = roles or []
    listing_fields = get_allowed_fields("seller_products", roles, "read") or None
    catalog_fields = get_allowed_fields("products", roles, "read") or None

    try:
        min_price_col = (
            func.min(SellerProduct.price)
            .over(partition_by=SellerProduct.product_id)
            .label("min_price")
        )

        query = (
            db.session.query(SellerProduct, min_price_col)
            .join(Product, Product.id == SellerProduct.product_id)
            .filter(
                Product.deleted_at.is_(None),
                SellerProduct.deleted_at.is_(None),
                SellerProduct.status == ProductStatus.ACTIVE,
                SellerProduct.stock > 0,
            )
        )

        search = filters.get("search")
        if search:
            like = f"%{search}%"
            query = query.filter(or_(
                Product.brand.ilike(like),
                Product.name.ilike(like),
                Product.model.ilike(like),
                SellerProduct.title.ilike(like),
            ))

        category_id = filters.get("category_id")
        if category_id:
            query = query.filter(Product.categories.any(Category.id == category_id))

        if filters.get("min_price") is not None:
            query = query.filter(SellerProduct.price >= filters["min_price"])
        if filters.get("max_price") is not None:
            query = query.filter(SellerProduct.price <= filters["max_price"])

        sort = filters.get("sort")
        sort_columns = {
            "price": SellerProduct.price,
            "title": SellerProduct.title,
            "created_at": SellerProduct.created_at,
        }
        if sort:
            descending = sort.startswith("-")
            column = sort_columns.get(sort.lstrip("-"))
            if column is not None:
                query = query.order_by(column.desc() if descending else column.asc())
        else:
            query = query.order_by(SellerProduct.price.asc())

        page = paginate_query(query, args=filters)

        items = []
        for row in page["items"]:
            sp, mp = row  # (SellerProduct, min_price)
            data = sp.to_dict(allowed_fields=listing_fields)
            catalog = sp.catalog.to_dict(allowed_fields=catalog_fields) if sp.catalog else {}
            # Merge catalog spec, keep listing keys authoritative.
            merged = {**catalog, **data}
            merged["seller_product_id"] = sp.id
            merged["min_price"] = float(mp) if mp is not None else None
            items.append(merged)
        page["items"] = items
        return page
    except Exception as e:
        logging.error(f"Failed to browse listings: {str(e)}")
        return None


def get_my_listings(filters=None, jwt_user_id=None, roles=None):
    """A seller's own listings (any non-deleted status). Admin sees all."""
    from app.utils.pagination import paginate_query
    filters = filters or {}
    roles = roles or []
    try:
        query = SellerProduct.query.filter(SellerProduct.deleted_at.is_(None))
        if not _is_admin(roles) and jwt_user_id is not None:
            query = query.filter(SellerProduct.user_id == int(jwt_user_id))

        search = filters.get("search")
        if search:
            query = query.filter(SellerProduct.title.ilike(f"%{search}%"))

        query = query.order_by(SellerProduct.id.asc())
        return paginate_query(query, args=filters)
    except Exception as e:
        logging.error(f"Failed to retrieve listings: {str(e)}")
        return None


def get_listing_by_id(listing_id, jwt_user_id=None, roles=None):
    """
    Single listing. Non-owner/anonymous may only see ACTIVE listings whose
    catalog product is live. Owner/admin see any non-deleted status.
    """
    roles = roles or []
    try:
        listing = SellerProduct.query.filter(
            SellerProduct.id == listing_id,
            SellerProduct.deleted_at.is_(None),
        ).first()
        if not listing:
            return None

        if listing.status == ProductStatus.ACTIVE and listing.catalog and listing.catalog.deleted_at is None:
            return listing

        is_owner = jwt_user_id is not None and listing.user_id == int(jwt_user_id)
        if _is_admin(roles) or is_owner:
            return listing
        return None
    except Exception as e:
        logging.error(f"Failed to retrieve listing {listing_id}: {str(e)}")
        return None


# =============================================================================
# CREATE (Option B: find-or-create catalog, then create listing PENDING)
# =============================================================================

def _resolve_seller_id(client_user_id, jwt_user_id, roles):
    if _is_admin(roles):
        if client_user_id and isinstance(client_user_id, int):
            return client_user_id
        return int(jwt_user_id)
    return int(jwt_user_id)


def find_or_create_catalog(data):
    """
    Option B dedupe: if barcode provided, reuse an existing non-deleted catalog
    product with that barcode; otherwise create a new catalog row.
    Returns (Product, error_or_None).
    """
    barcode = data.get("barcode")
    catalog = None
    if barcode:
        catalog = Product.query.filter(
            Product.barcode == barcode,
            Product.deleted_at.is_(None),
        ).first()

    if catalog is not None:
        return catalog, None

    catalog = Product(
        brand=data["brand"],
        name=data["name"],
        description=data.get("description"),
        model=data.get("model"),
        color=data.get("color"),
        size=data.get("size"),
        barcode=barcode,
        specifications=data.get("specifications"),
    )

    category_ids = data.get("category_ids") or []
    if category_ids:
        categories = Category.query.filter(Category.id.in_(category_ids)).all()
        if len(categories) != len(category_ids):
            return None, ValidationResponse(success=False, message="Some category IDs not found")
        catalog.categories = categories

    db.session.add(catalog)
    db.session.flush()  # assign catalog.id
    return catalog, None


def create_listing(data, jwt_user_id, roles):
    """
    Create a seller listing (PENDING). Find-or-creates the catalog product.
    Enforces one listing per seller per catalog product.
    """
    from app.permissions.field_filter import get_allowed_fields

    if not get_allowed_fields("seller_products", roles, "create"):
        return ValidationResponse(success=False, message="Your role does not have permission to create listings")

    seller_id = _resolve_seller_id(data.get("user_id"), jwt_user_id, roles)

    try:
        catalog, err = find_or_create_catalog(data)
        if err is not None:
            db.session.rollback()
            return err

        # One listing per seller per catalog product.
        existing = SellerProduct.query.filter(
            SellerProduct.product_id == catalog.id,
            SellerProduct.user_id == seller_id,
            SellerProduct.deleted_at.is_(None),
        ).first()
        if existing:
            db.session.rollback()
            return ValidationResponse(
                success=False,
                message="You already have a listing for this product.",
            )

        listing = SellerProduct(
            product_id=catalog.id,
            user_id=seller_id,
            title=data["title"],
            slug=generate_listing_slug(data["title"]),
            price=data["price"],
            stock=data.get("stock", 0),
            status=ProductStatus.PENDING,   # always PENDING on create (awaits admin)
            sku=data.get("sku"),
        )
        db.session.add(listing)
        db.session.commit()
        logging.info(f"Listing created: {listing.id} (product {catalog.id}, seller {seller_id})")
        return listing

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Integrity error creating listing: {str(e)}")
        return ValidationResponse(success=False, message="Could not create listing (duplicate or constraint).")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create listing: {str(e)}")
        return None


# =============================================================================
# UPDATE (seller edits own; admin drives status transitions)
# =============================================================================

def update_listing(listing_id, update_data, jwt_user_id, roles):
    from app.permissions.field_filter import get_allowed_fields
    try:
        listing = SellerProduct.query.filter(
            SellerProduct.id == listing_id,
            SellerProduct.deleted_at.is_(None),
        ).first()
        if not listing:
            return ValidationResponse(success=False, message="Listing not found")

        is_admin = _is_admin(roles)
        if listing.user_id != int(jwt_user_id) and not is_admin:
            return ValidationResponse(success=False, message="Unauthorized to update this listing")

        allowed = get_allowed_fields("seller_products", roles, "update")
        blocked = set(update_data.keys()) - allowed
        if blocked and not (set(update_data.keys()) & allowed):
            return ValidationResponse(
                success=False,
                message=f"Your role does not have permission to update: {', '.join(blocked)}",
            )

        # Status transition (with side effects).
        new_status_raw = update_data.pop("status", None)
        if new_status_raw is not None and "status" in allowed:
            try:
                new_status = ProductStatus(new_status_raw)
            except ValueError:
                return ValidationResponse(success=False, message=f"Invalid status: {new_status_raw}")

            if not is_transition_allowed(listing.status, new_status, is_admin):
                return ValidationResponse(
                    success=False,
                    message=(f"Invalid status transition from {listing.status.value} "
                             f"to {new_status.value} for your role."),
                )

            if new_status != listing.status:
                listing.status = new_status
                if new_status == ProductStatus.REJECTED:
                    listing.deleted_at = func.now()
                    if listing.images:
                        listing.images = None
                elif new_status in (ProductStatus.INACTIVE, ProductStatus.SUSPENDED):
                    _cascade_pending_order_items(listing.id)

        # Scalar fields.
        for key, value in update_data.items():
            if key in allowed and hasattr(listing, key):
                setattr(listing, key, value)

        if "title" in update_data and "title" in allowed:
            listing.slug = generate_listing_slug(listing.title)

        db.session.commit()
        logging.info(f"Listing updated: {listing.id}")
        return listing

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Integrity error updating listing: {str(e)}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update listing: {str(e)}")
        return None


# =============================================================================
# DELETE (soft default / hard superadmin; PAID-order guard)
# =============================================================================

def delete_listing(listing_id, jwt_user_id, roles, action="soft"):
    from app.permissions.field_filter import get_delete_policy
    try:
        listing = SellerProduct.query.filter(SellerProduct.id == listing_id).first()
        if not listing:
            return ValidationResponse(success=False, message="Listing not found", status_code=404)

        delete_policy = get_delete_policy("seller_products", roles)
        if delete_policy is None:
            return ValidationResponse(success=False, message="Your role does not have permission to delete listings", status_code=403)

        is_admin = _is_admin(roles)
        if listing.user_id != int(jwt_user_id) and not is_admin:
            return ValidationResponse(success=False, message="Unauthorized to delete this listing", status_code=403)

        # Block deletion when linked to active PAID orders.
        from app.models.order_model import Order, OrderStatus
        from app.models.order_items_model import Order_item
        active_order_count = Order_item.query.join(
            Order, Order_item.order_id == Order.id
        ).filter(
            Order_item.seller_product_id == listing_id,
            Order.status == OrderStatus.PAID,
            Order.deleted_at.is_(None),
        ).count()
        if active_order_count > 0:
            return ValidationResponse(
                success=False,
                message=f"Unable to delete this listing. It is linked to {active_order_count} active order(s). Complete or cancel them first.",
                status_code=409,
            )

        if action == "hard":
            if delete_policy != "hard":
                return ValidationResponse(success=False, message="Only superadmin can perform hard delete", status_code=403)
            _remove_listing_images(listing)
            db.session.delete(listing)
            db.session.commit()
            logging.info(f"Listing hard-deleted: {listing_id}")
            return ValidationResponse(success=True, message=f"Listing {listing_id} permanently deleted", status_code=200)

        if listing.deleted_at is not None:
            return ValidationResponse(success=False, message="Listing is already deleted", status_code=400)
        _remove_listing_images(listing)
        listing.images = None
        listing.deleted_at = func.now()
        db.session.commit()
        logging.info(f"Listing soft-deleted: {listing_id}")
        return ValidationResponse(success=True, message=f"Listing {listing_id} soft-deleted", status_code=200)

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Integrity error deleting listing {listing_id}: {str(e)}")
        return ValidationResponse(success=False, message="Cannot delete due to database constraints.", status_code=409)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete listing {listing_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while deleting the listing.", status_code=500)


def _remove_listing_images(listing):
    import shutil
    uploads_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')
    folder = os.path.join(uploads_root, 'seller_products', listing.uuid)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
        logging.info(f"Deleted image folder for listing {listing.id}: {folder}")


# =============================================================================
# CART CASCADE (INACTIVE/SUSPENDED) — keyed on seller_product_id
# =============================================================================

def _cascade_pending_order_items(seller_product_id):
    """
    Soft-delete this listing's order_items in PENDING carts, then recompute
    affected order totals. Cross-seller safe (keys on seller_product_id).
    Does NOT commit (caller commits).
    """
    from app.models.order_model import Order, OrderStatus
    from app.models.order_items_model import Order_item

    items = Order_item.query.join(
        Order, Order_item.order_id == Order.id
    ).filter(
        Order_item.seller_product_id == seller_product_id,
        Order_item.deleted_at.is_(None),
        Order.status == OrderStatus.PENDING,
        Order.deleted_at.is_(None),
    ).all()

    affected = set()
    for item in items:
        item.deleted_at = func.now()
        affected.add(item.order_id)

    for order_id in affected:
        _recalculate_order_totals(order_id)


def _recalculate_order_totals(order_id):
    from flask import current_app
    from app.models.order_model import Order
    from app.models.order_items_model import Order_item

    order = Order.query.get(order_id)
    if order is None:
        return

    live_items = Order_item.query.filter(
        Order_item.order_id == order_id,
        Order_item.deleted_at.is_(None),
    ).all()

    subtotal = sum(float(i.compound_price) for i in live_items)
    discount_percent = float(order.discount_percent or 0)
    discount_amount = round(subtotal * (discount_percent / 100), 2)
    after_discount = subtotal - discount_amount
    tax_percent = float(order.tax_percent if order.tax_percent is not None
                        else current_app.config.get('TAX_PERCENT', 11))
    tax_amount = round(after_discount * (tax_percent / 100), 2)

    order.subtotal = subtotal
    order.discount_amount = discount_amount
    order.tax_percent = tax_percent
    order.tax_amount = tax_amount
    order.total = round(after_discount + tax_amount, 2)
