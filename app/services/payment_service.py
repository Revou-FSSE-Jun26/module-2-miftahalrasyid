import logging
from app.extensions import db
from app.models import Order, OrderStatus, Product
from app.models.order_items_model import Order_item
from app.models.address_model import Address
from app.services import ValidationResponse


def process_payment(order_id, jwt_user_id, address_id=None):
    """
    Process payment for a PENDING order.
    
    1. Validates order exists, belongs to user, and is PENDING
    2. Resolves address: explicit address_id > user's default address
    3. Validates stock availability for all items
    4. Deducts stock
    5. Sets address_id on order
    6. Transitions status PENDING → PAID
    
    Args:
        order_id: Order ID to pay
        jwt_user_id: Authenticated user's ID
        address_id: Optional specific address ID to use (overrides default)
    
    Returns:
        Order on success, ValidationResponse on error
    """
    try:
        user_id = int(jwt_user_id)

        # 1. Find order
        order = Order.query.filter(
            Order.id == order_id,
            Order.deleted_at.is_(None)
        ).first()

        if not order:
            return ValidationResponse(success=False, message="Order not found", status_code=404)

        # 2. Ownership check
        if order.user_id != user_id:
            return ValidationResponse(success=False, message="Unauthorized to pay for this order", status_code=403)

        # 3. Must be PENDING
        if order.status != OrderStatus.PENDING:
            return ValidationResponse(
                success=False,
                message=f"Only PENDING orders can be paid. Current status: {order.status.value}",
                status_code=400
            )

        # 4. Resolve address
        resolved_address = None
        if address_id:
            resolved_address = Address.query.filter_by(id=address_id, user_id=user_id).first()
            if not resolved_address:
                return ValidationResponse(success=False, message="Address not found", status_code=404)
        else:
            # Use default address
            resolved_address = Address.query.filter_by(user_id=user_id, is_default=True).first()
            if not resolved_address:
                return ValidationResponse(success=False, message="Default address is not set", status_code=400)

        # 5. Validate stock and deduct
        order_items = Order_item.query.filter(
            Order_item.order_id == order_id,
            Order_item.deleted_at.is_(None)
        ).all()

        if not order_items:
            return ValidationResponse(success=False, message="Order has no items", status_code=400)

        for item in order_items:
            product = Product.query.filter(
                Product.id == item.product_id,
                Product.deleted_at.is_(None),
                Product.is_active == True
            ).first()

            if not product:
                return ValidationResponse(
                    success=False,
                    message=f"Product with id '{item.product_id}' is no longer available",
                    status_code=400
                )

            if product.stock < item.quantity:
                return ValidationResponse(
                    success=False,
                    message=f"Insufficient stock for product '{product.name}'. Available: {product.stock}, required: {item.quantity}",
                    status_code=400
                )

        # All checks passed — deduct stock
        for item in order_items:
            product = Product.query.get(item.product_id)
            product.stock -= item.quantity

        # 6. Set address and transition to PAID
        order.address_id = resolved_address.id
        order.status = OrderStatus.PAID

        db.session.commit()
        logging.info(f"Payment processed for order {order_id}, address_id={resolved_address.id}")
        return order

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to process payment for order {order_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred during payment processing", status_code=500)
