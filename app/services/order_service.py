from app.extensions import db
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.models import Order, OrderStatus, Product, UserRole
from app.models.order_items_model import Order_item
from . import ValidationResponse


def get_all_orders(jwt_user_id, roles, filters=None):
    """
    Get orders based on role with pagination, filtering and sorting.
    - Admin/Superadmin: all orders (not soft-deleted)
    - Seller: orders containing their products
    - Buyer: only their own orders

    Ownership scoping is enforced here and cannot be overridden by `filters`.

    Args:
        filters: validated query-args dict (page, per_page, status, sort). All optional.
    """
    from app.utils.pagination import paginate_query
    filters = filters or {}
    try:
        is_admin = any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)

        if is_admin:
            query = Order.query.filter(Order.deleted_at.is_(None))
        elif UserRole.SELLER.value in roles:
            query = Order.query.filter(
                Order.deleted_at.is_(None),
                Order.id.in_(
                    db.session.query(Order_item.order_id).join(
                        Product, Order_item.product_id == Product.id
                    ).filter(Product.user_id == int(jwt_user_id))
                )
            )
        else:
            query = Order.query.filter(
                Order.deleted_at.is_(None),
                Order.user_id == int(jwt_user_id)
            )

        status = filters.get("status")
        if status:
            try:
                query = query.filter(Order.status == OrderStatus(status))
            except ValueError:
                pass

        sort = filters.get("sort")
        sort_columns = {"total": Order.total, "created_at": Order.created_at}
        if sort:
            descending = sort.startswith("-")
            column = sort_columns.get(sort.lstrip("-"))
            if column is not None:
                query = query.order_by(column.desc() if descending else column.asc())
        else:
            query = query.order_by(Order.id.asc())

        return paginate_query(query, args=filters)
    except Exception as e:
        logging.error(f"Failed to retrieve orders: {str(e)}")
        return None


def get_order_by_id(order_id, jwt_user_id, roles):
    """
    Get a single order by ID with ownership/role check.
    """
    try:
        order = Order.query.filter(
            Order.id == order_id,
            Order.deleted_at.is_(None)
        ).first()

        if not order:
            return None

        is_admin = any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)

        if is_admin:
            return order

        # Seller: can view if order contains their product
        if UserRole.SELLER.value in roles:
            has_seller_product = Order_item.query.join(
                Product, Order_item.product_id == Product.id
            ).filter(
                Order_item.order_id == order_id,
                Product.user_id == int(jwt_user_id)
            ).first()
            if has_seller_product:
                return order

        # Buyer: own order only
        if order.user_id == int(jwt_user_id):
            return order

        return None
    except Exception as e:
        logging.error(f"Failed to retrieve order {order_id}: {str(e)}")
        return None


def create_order(order_instance, items_data, jwt_user_id, roles):
    """
    Create a new order with order items.
    Buyer creates orders. Admin/Superadmin can create on behalf of a user.
    
    Args:
        order_instance: Order model instance (name set by schema)
        items_data: list of {"product_id": int, "quantity": int}
        jwt_user_id: Authenticated user's ID
        roles: User's roles from JWT
    
    Returns:
        Order on success, ValidationResponse on error, None on failure
    """
    from app.permissions.field_filter import get_allowed_fields

    # RBAC: check create permission
    allowed = get_allowed_fields("orders", roles, "create")
    if not allowed:
        return ValidationResponse(success=False, message="Your role does not have permission to create orders")

    if not items_data or len(items_data) == 0:
        return ValidationResponse(success=False, message="Order must contain at least one item")

    # Set user_id
    order_instance.user_id = int(jwt_user_id)
    # Orders start as PENDING (cart). Stock is NOT deducted until payment.
    order_instance.status = OrderStatus.PENDING
    # address_id can be null at this stage (set during payment)

    try:
        # Validate items and calculate total
        total = 0
        order_items = []
        seen_product_ids = set()

        for item in items_data:
            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if not product_id or not quantity:
                return ValidationResponse(success=False, message="Each item must have product_id and quantity")

            if not isinstance(quantity, int) or quantity < 1:
                return ValidationResponse(success=False, message="Quantity must be a positive integer")

            if product_id in seen_product_ids:
                return ValidationResponse(success=False, message="Duplicate product in order items")
            seen_product_ids.add(product_id)

            # Verify product exists and is active
            product = Product.query.filter(
                Product.id == product_id,
                Product.deleted_at.is_(None),
                Product.is_active == True
            ).first()

            if not product:
                return ValidationResponse(success=False, message=f"Product with id '{product_id}' is not found or not available")

            # Self-purchase prevention: seller cannot order their own products
            if product.user_id == int(jwt_user_id):
                return ValidationResponse(success=False, message=f"You cannot order your own product (product_id: {product_id})")

            # Check stock availability (reserve check only, no deduction yet)
            if product.stock < quantity:
                return ValidationResponse(success=False, message=f"Insufficient stock for product '{product.name}'. Available: {product.stock}")

            compound_price = float(product.price) * quantity
            total += compound_price

            order_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "compound_price": compound_price,
                "product": product
            })

        # Calculate pricing: subtotal → discount → tax → total
        from flask import current_app
        subtotal = total
        discount_percent = 0  # TODO: apply coupon/promo logic here
        discount_amount = round(subtotal * (discount_percent / 100), 2)
        after_discount = subtotal - discount_amount
        tax_percent = current_app.config.get('TAX_PERCENT', 11)
        tax_amount = round(after_discount * (tax_percent / 100), 2)
        final_total = round(after_discount + tax_amount, 2)

        order_instance.subtotal = subtotal
        order_instance.discount_percent = discount_percent
        order_instance.discount_amount = discount_amount
        order_instance.tax_percent = tax_percent
        order_instance.tax_amount = tax_amount
        order_instance.total = final_total

        # Save order first to get order.id
        db.session.add(order_instance)
        db.session.flush()

        # Create order items (NO stock deduction — deducted on payment)
        for item_data in order_items:
            order_item = Order_item(
                order_id=order_instance.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                compound_price=item_data["compound_price"]
            )
            db.session.add(order_item)

        db.session.commit()
        logging.info(f"Order created successfully: {order_instance.id}")
        return order_instance

    except IntegrityError as e:
        db.session.rollback()
        error_msg = str(e.orig) if e.orig else str(e)
        if "uq_order_product" in error_msg:
            return ValidationResponse(success=False, message="Product already exists in this order")
        logging.error(f"Integrity error creating order: {error_msg}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to create order: {str(e)}")
        return None


def update_order(order_id, update_data, jwt_user_id, roles):
    """
    Update an order (mainly status transitions).
    Seller can update status for orders containing their products.
    Admin/Superadmin can update any order.
    
    Args:
        order_id: Order ID to update
        update_data: Dict of fields to update
        jwt_user_id: Authenticated user's ID
        roles: User's roles from JWT
    
    Returns:
        Order on success, ValidationResponse on error, None on failure
    """
    from app.permissions.field_filter import get_allowed_fields

    try:
        order = Order.query.filter(
            Order.id == order_id,
            Order.deleted_at.is_(None)
        ).first()

        if not order:
            return ValidationResponse(success=False, message="Order not found")

        # Authorization check
        is_admin = any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)

        if not is_admin:
            # Seller: can only update orders containing their products
            if UserRole.SELLER.value in roles:
                has_seller_product = Order_item.query.join(
                    Product, Order_item.product_id == Product.id
                ).filter(
                    Order_item.order_id == order_id,
                    Product.user_id == int(jwt_user_id)
                ).first()
                if not has_seller_product:
                    return ValidationResponse(success=False, message="Unauthorized to update this order")
            else:
                return ValidationResponse(success=False, message="Your role does not have permission to update orders")

        # RBAC: filter fields by role
        allowed = get_allowed_fields("orders", roles, "update")
        if not allowed:
            return ValidationResponse(success=False, message="Your role does not have permission to update orders")

        # Validate status transition if status is being updated
        new_status = update_data.get("status")
        if new_status:
            try:
                new_status_enum = OrderStatus(new_status)
            except ValueError:
                return ValidationResponse(success=False, message=f"Invalid status: {new_status}")

            # Validate status transition: PAID → COMPLETED or PAID → CANCELED only
            valid = _validate_status_transition(order.status, new_status_enum)
            if not valid:
                return ValidationResponse(
                    success=False,
                    message=f"Invalid status transition from {order.status.value} to {new_status_enum.value}. Allowed: PENDING → PAID, PAID → COMPLETED or PAID → CANCELED"
                )

            # If transitioning to CANCELED: refund the buyer (if paid via gateway),
            # then restore stock to the seller.
            if new_status_enum == OrderStatus.CANCELED:
                refund_result = _refund_payment(order)
                if isinstance(refund_result, ValidationResponse) and not refund_result.success:
                    # Gateway refused the refund — abort the cancellation entirely.
                    # Do NOT restore stock or change status, so money and inventory stay consistent.
                    db.session.rollback()
                    return refund_result
                _restore_stock(order.id)

        # Apply allowed fields
        for key, value in update_data.items():
            if key in allowed and hasattr(order, key):
                if key == "status":
                    order.status = OrderStatus(value)
                else:
                    setattr(order, key, value)

        db.session.commit()
        logging.info(f"Order updated successfully: {order.id}")
        return order

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to update order: {str(e)}")
        return None


def delete_order(order_id, jwt_user_id, roles, action="soft"):
    """
    Delete an order by ID.
    Default = soft delete (set deleted_at).
    Superadmin can pass action="hard" to permanently remove.
    Buyer can only soft-delete own PENDING orders.
    
    Args:
        order_id: Order ID to delete
        jwt_user_id: Authenticated user's ID
        roles: User's roles from JWT
        action: "soft" (default) or "hard" (superadmin only)
    
    Returns:
        dict on success, ValidationResponse on error, None on failure
    """
    from app.permissions.field_filter import get_delete_policy

    try:
        order = Order.query.filter(Order.id == order_id).first()

        if not order:
            return ValidationResponse(success=False, message="Order not found", status_code=404)

        # Check delete permission
        delete_policy = get_delete_policy("orders", roles)
        if delete_policy is None:
            return ValidationResponse(success=False, message="Your role does not have permission to delete orders", status_code=403)

        # Authorization
        is_admin = any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)

        if not is_admin:
            # Buyer can only delete own orders with COMPLETED or CANCELED status
            if order.user_id != int(jwt_user_id):
                return ValidationResponse(success=False, message="Unauthorized to delete this order", status_code=403)
            if order.status not in (OrderStatus.COMPLETED, OrderStatus.CANCELED):
                return ValidationResponse(success=False, message="Can only delete orders with COMPLETED or CANCELED status", status_code=400)

        # Verify all products in this order still exist (not hard-deleted)
        order_items_list = Order_item.query.filter(
            Order_item.order_id == order_id,
            Order_item.deleted_at.is_(None)
        ).all()
        for item in order_items_list:
            product = Product.query.get(item.product_id)
            if product is None:
                return ValidationResponse(
                    success=False,
                    message=f"Unable to process this order deletion. Product (ID: {item.product_id}) has been permanently removed from the system. Please contact an administrator.",
                    status_code=409
                )

        # Hard delete: only superadmin with action="hard"
        if action == "hard":
            if delete_policy != "hard":
                return ValidationResponse(success=False, message="Only superadmin can perform hard delete", status_code=403)
            # Restore stock before hard delete
            _restore_stock(order_id)
            db.session.delete(order)
            db.session.commit()
            logging.info(f"Order hard-deleted: {order_id}")
            return ValidationResponse(success=True, message=f"Order {order_id} permanently deleted", status_code=200)

        # Soft delete (default)
        if order.deleted_at is not None:
            return ValidationResponse(success=False, message="Order is already deleted", status_code=400)

        # No stock restoration needed for COMPLETED/CANCELED orders (already handled during status transition)
        order.deleted_at = func.now()
        db.session.commit()
        logging.info(f"Order soft-deleted: {order_id}")
        return ValidationResponse(success=True, message=f"Order {order_id} soft-deleted", status_code=200)

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Integrity error deleting order {order_id}: {str(e)}")
        return ValidationResponse(success=False, message="Cannot delete this order due to database integrity constraints.", status_code=409)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete order {order_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while deleting the order.", status_code=500)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _validate_status_transition(current_status, new_status):
    """
    Validate that a status transition follows the allowed rules:
    PENDING -> PAID (via payment endpoint)
    PAID -> COMPLETED (seller fulfills)
    PAID -> CANCELED (seller rejects / buyer cancels)
    No transition back to PENDING is allowed.
    """
    allowed_transitions = {
        OrderStatus.PENDING: {OrderStatus.PAID},
        OrderStatus.PAID: {OrderStatus.COMPLETED, OrderStatus.CANCELED},
    }

    allowed = allowed_transitions.get(current_status, set())
    return new_status in allowed


def _refund_payment(order):
    """
    Issue a full refund through Midtrans for a PAID order being canceled.

    Behavior:
      - Orders with no payment_ref (legacy/seeded, or never paid via the gateway)
        skip the gateway call entirely — nothing to refund. Returns success.
      - Orders whose gateway payment_status is "settlement" are refunded for the
        full order total. On success payment_status is set to "refund".
      - Any gateway error returns a failed ValidationResponse so the caller can
        abort the cancellation (keeping money and stock consistent).

    Returns:
        ValidationResponse (success=True when refund done or not needed;
        success=False when the gateway refused).
    """
    import time
    import logging

    # No gateway reference -> not a real Midtrans payment; nothing to refund.
    if not order.payment_ref:
        return ValidationResponse(success=True, message="No gateway payment to refund", status_code=200)

    # Only settled payments can be refunded. Non-settled (e.g. still pending) are
    # canceled at the gateway instead; treat as no-op here to avoid false refunds.
    if order.payment_status != "settlement":
        logging.info(
            f"Order {order.id} cancel: payment_status='{order.payment_status}', "
            f"skipping refund (not a settled payment)"
        )
        return ValidationResponse(success=True, message="No settled payment to refund", status_code=200)

    try:
        from app.services.midtrans_client import get_snap_client

        snap = get_snap_client()
        snap.transaction.refund(order.payment_ref, {
            "refund_key": f"refund-{order.id}-{int(time.time())}",
            "amount": int(round(float(order.total))),
            "reason": "Order canceled",
        })
        order.payment_status = "refund"
        logging.info(f"Refund issued for order {order.id} (ref={order.payment_ref})")
        return ValidationResponse(success=True, message="Refund issued", status_code=200)
    except Exception as e:
        logging.error(f"Refund failed for order {order.id} (ref={order.payment_ref}): {str(e)}")
        return ValidationResponse(
            success=False,
            message="Failed to process refund with the payment gateway. Cancellation aborted.",
            status_code=502
        )


def _restore_stock(order_id):
    """
    Restore product stock for all items in an order.
    Used when cancelling/deleting a PENDING order.
    """
    order_items = Order_item.query.filter(
        Order_item.order_id == order_id,
        Order_item.deleted_at.is_(None)
    ).all()

    for item in order_items:
        product = Product.query.get(item.product_id)
        if product:
            product.stock += item.quantity


def get_order_items(order_id):
    """
    Get all items for an order.
    """
    try:
        items = Order_item.query.filter(
            Order_item.order_id == order_id,
            Order_item.deleted_at.is_(None)
        ).all()
        return [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "compound_price": float(item.compound_price),
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ]
    except Exception as e:
        logging.error(f"Failed to retrieve order items for order {order_id}: {str(e)}")
        return []
