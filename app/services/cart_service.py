from app.extensions import db
import logging
from sqlalchemy.exc import IntegrityError
from app.models import CartItem, Product, SellerProduct, ProductStatus
from . import ValidationResponse


def _get_purchasable_listing(seller_product_id):
    """
    Return the listing only if it is purchasable: ACTIVE, not soft-deleted, and
    its catalog product not soft-deleted. Mirrors the purchase gate in
    create_order so a listing cannot sit in a cart in a state it can't be
    ordered in. Returns the SellerProduct or None.
    """
    return (
        SellerProduct.query
        .join(Product, Product.id == SellerProduct.product_id)
        .filter(
            SellerProduct.id == seller_product_id,
            SellerProduct.deleted_at.is_(None),
            SellerProduct.status == ProductStatus.ACTIVE,
            Product.deleted_at.is_(None),
        ).first()
    )


def _serialize_line(item, listing):
    """Build the enriched cart-line dict (live price/stock from the listing)."""
    price = float(listing.price) if listing and listing.price is not None else 0.0
    stock = listing.stock if listing else 0
    return {
        "id": item.id,
        "seller_product_id": item.seller_product_id,
        "product_id": listing.product_id if listing else None,
        "title": listing.title if listing else None,
        "price": price,
        "quantity": item.quantity,
        "line_total": round(price * item.quantity, 2),
        "stock": stock,
        # A line the buyer can still check out: listing live AND enough stock.
        "available": bool(listing) and stock >= item.quantity,
        "images": (listing.images or []) if listing else [],
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def get_cart(jwt_user_id, filters=None):
    """
    Return the caller's cart lines (paginated) enriched with live listing data,
    plus a summary. Lines are read-live: price/stock/availability reflect the
    listing right now, so a cart never shows a stale price.
    """
    from app.utils.pagination import paginate_query
    filters = filters or {}
    try:
        query = (
            CartItem.query
            .filter(CartItem.user_id == int(jwt_user_id))
            .order_by(CartItem.created_at.desc(), CartItem.id.desc())
        )
        page = paginate_query(query, args=filters)

        # Resolve listings for the current page in one query.
        listing_ids = [i.seller_product_id for i in page["items"]]
        listing_by_id = {}
        if listing_ids:
            for sp in SellerProduct.query.filter(SellerProduct.id.in_(listing_ids)).all():
                listing_by_id[sp.id] = sp

        lines = [
            _serialize_line(item, listing_by_id.get(item.seller_product_id))
            for item in page["items"]
        ]

        subtotal = round(sum(l["line_total"] for l in lines if l["available"]), 2)
        return {
            "items": lines,
            "summary": {
                "item_count": page["total"],
                "subtotal": subtotal,
                "has_unavailable": any(not l["available"] for l in lines),
            },
            "page": page["page"],
            "per_page": page["per_page"],
            "count": page["total"],
        }
    except Exception as e:
        logging.error(f"Failed to retrieve cart for user {jwt_user_id}: {str(e)}")
        return None


def add_to_cart(jwt_user_id, seller_product_id, quantity):
    """
    Add a listing to the caller's cart. If it's already there, bump the quantity
    (idempotent-ish add). Validates the listing is purchasable, blocks adding the
    caller's own listing, and caps the resulting quantity at available stock.

    Returns the CartItem on success, ValidationResponse on validation error,
    None on unexpected failure.
    """
    try:
        if not isinstance(quantity, int) or quantity < 1:
            return ValidationResponse(success=False, message="Quantity must be a positive integer")

        listing = _get_purchasable_listing(seller_product_id)
        if not listing:
            return ValidationResponse(
                success=False,
                message=f"Listing with id '{seller_product_id}' is currently unavailable",
            )

        # Self-purchase prevention (same rule as create_order).
        if listing.user_id == int(jwt_user_id):
            return ValidationResponse(success=False, message="You cannot add your own listing to the cart")

        existing = CartItem.query.filter_by(
            user_id=int(jwt_user_id),
            seller_product_id=seller_product_id,
        ).first()

        new_qty = (existing.quantity if existing else 0) + quantity
        if listing.stock < new_qty:
            return ValidationResponse(
                success=False,
                message=f"Insufficient stock for '{listing.title}'. Available: {listing.stock}",
            )

        if existing:
            existing.quantity = new_qty
            item = existing
        else:
            item = CartItem(
                user_id=int(jwt_user_id),
                seller_product_id=seller_product_id,
                quantity=quantity,
            )
            db.session.add(item)

        db.session.commit()
        logging.info(f"Cart add: user={jwt_user_id} listing={seller_product_id} qty={item.quantity}")
        return item

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Integrity error adding to cart: {str(e)}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to add to cart: {str(e)}")
        return None


def update_cart_item(jwt_user_id, cart_item_id, quantity):
    """
    Set an absolute quantity for a cart line the caller owns. Caps at live stock.
    Returns CartItem / ValidationResponse / None.
    """
    try:
        if not isinstance(quantity, int) or quantity < 1:
            return ValidationResponse(success=False, message="Quantity must be a positive integer", status_code=422)

        item = CartItem.query.filter_by(id=cart_item_id, user_id=int(jwt_user_id)).first()
        if not item:
            return ValidationResponse(success=False, message="Cart item not found", status_code=404)

        listing = _get_purchasable_listing(item.seller_product_id)
        if not listing:
            return ValidationResponse(success=False, message="This listing is no longer available", status_code=400)

        if listing.stock < quantity:
            return ValidationResponse(
                success=False,
                message=f"Insufficient stock for '{listing.title}'. Available: {listing.stock}",
                status_code=400,
            )

        item.quantity = quantity
        db.session.commit()
        logging.info(f"Cart update: user={jwt_user_id} item={cart_item_id} qty={quantity}")
        return item

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update cart item {cart_item_id}: {str(e)}")
        return None


def remove_cart_item(jwt_user_id, cart_item_id):
    """Hard-delete a single cart line the caller owns. Cart lines are transient,
    so there is no soft delete. Returns ValidationResponse (success/failure)."""
    try:
        item = CartItem.query.filter_by(id=cart_item_id, user_id=int(jwt_user_id)).first()
        if not item:
            return ValidationResponse(success=False, message="Cart item not found", status_code=404)

        db.session.delete(item)
        db.session.commit()
        logging.info(f"Cart remove: user={jwt_user_id} item={cart_item_id}")
        return ValidationResponse(success=True, message="Item removed from cart", status_code=200)

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to remove cart item {cart_item_id}: {str(e)}")
        return ValidationResponse(success=False, message="Failed to remove item from cart", status_code=500)


def clear_cart(jwt_user_id):
    """Empty the caller's entire cart. Returns ValidationResponse with a count."""
    try:
        deleted = CartItem.query.filter_by(user_id=int(jwt_user_id)).delete()
        db.session.commit()
        logging.info(f"Cart clear: user={jwt_user_id} removed={deleted}")
        return ValidationResponse(success=True, message=f"Cart cleared ({deleted} item(s) removed)", status_code=200)

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to clear cart for user {jwt_user_id}: {str(e)}")
        return ValidationResponse(success=False, message="Failed to clear cart", status_code=500)
