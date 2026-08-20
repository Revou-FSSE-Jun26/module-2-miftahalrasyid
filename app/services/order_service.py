from app.extensions import db
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.models import Order, OrderStatus, Product, UserRole
from app.models.order_items_model import Order_item
from . import ValidationResponse


def get_all_orders(jwt_user_id, roles):
    """
    Get orders based on role:
    - Admin/Superadmin: all orders (not soft-deleted)
    - Seller: orders containing their products
    - Buyer: only their own orders
    """
    try:
        is_admin = any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)

        if is_admin:
            orders = Order.query.filter(Order.deleted_at.is_(None)).all()
        elif UserRole.SELLER.value in roles:
            # Orders that contain at least one product owned by this seller
            orders = Order.query.filter(
                Order.deleted_at.is_(None),
                Order.id.in_(
                    db.session.query(Order_item.order_id).join(
                        Product, Order_item.product_id == Product.id
                    ).filter(Product.user_id == int(jwt_user_id))
                )
            ).all()
        else:
            # Buyer: own orders only
            orders = Order.query.filter(
                Order.deleted_at.is_(None),
                Order.user_id == int(jwt_user_id)
            ).all()

        return orders
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
    order_instance.status = OrderStatus.PAID

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

            # Check stock
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

        order_instance.total = total

        # Save order first to get order.id
        db.session.add(order_instance)
        db.session.flush()

        # Create order items and deduct stock
        for item_data in order_items:
            order_item = Order_item(
                order_id=order_instance.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                compound_price=item_data["compound_price"]
            )
            db.session.add(order_item)

            # Deduct stock
            item_data["product"].stock -= item_data["quantity"]

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
                    message=f"Invalid status transition from {order.status.value} to {new_status_enum.value}. Allowed: PAID → COMPLETED or PAID → CANCELED"
                )

            # If transitioning to CANCELED, restore stock
            if new_status_enum == OrderStatus.CANCELED:
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
            return ValidationResponse(success=False, message="Order not found")

        # Check delete permission
        delete_policy = get_delete_policy("orders", roles)
        if delete_policy is None:
            return ValidationResponse(success=False, message="Your role does not have permission to delete orders")

        # Authorization
        is_admin = any(r in (UserRole.ADMIN.value, UserRole.SUPERADMIN.value) for r in roles)

        if not is_admin:
            # Buyer can only cancel own PAID orders
            if order.user_id != int(jwt_user_id):
                return ValidationResponse(success=False, message="Unauthorized to delete this order")
            if order.status != OrderStatus.PAID:
                return ValidationResponse(success=False, message="Can only cancel orders with PAID status")

        # Hard delete: only superadmin with action="hard"
        if action == "hard":
            if delete_policy != "hard":
                return ValidationResponse(success=False, message="Only superadmin can perform hard delete")
            # Restore stock before hard delete
            _restore_stock(order_id)
            db.session.delete(order)
            db.session.commit()
            logging.info(f"Order hard-deleted: {order_id}")
            return {"message": f"Order {order_id} permanently deleted"}

        # Soft delete (default)
        if order.deleted_at is not None:
            return ValidationResponse(success=False, message="Order is already deleted")

        # Restore stock on cancellation if order is PAID
        if order.status == OrderStatus.PAID:
            _restore_stock(order_id)

        order.deleted_at = func.now()
        db.session.commit()
        logging.info(f"Order soft-deleted: {order_id}")
        return {"message": f"Order {order_id} soft-deleted"}

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete order {order_id}: {str(e)}")
        return None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _validate_status_transition(current_status, new_status):
    """
    Validate that a status transition follows the allowed rules:
    PAID -> COMPLETED (seller accepts)
    PAID -> CANCELED (seller rejects / cancels)
    No other transitions allowed.
    """
    allowed_transitions = {
        OrderStatus.PAID: {OrderStatus.COMPLETED, OrderStatus.CANCELED},
    }

    allowed = allowed_transitions.get(current_status, set())
    return new_status in allowed


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
