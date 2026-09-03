import logging
import time
import hashlib
from flask import current_app
from app.extensions import db
from app.models import Order, OrderStatus, Product
from app.models.order_items_model import Order_item
from app.models.address_model import Address
from app.models.user_model import User
from app.services import ValidationResponse
from app.services.midtrans_client import get_snap_client


def initiate_payment(order_id, jwt_user_id, address_id=None):
    """
    Initiate payment for a PENDING order via Midtrans Snap.

    This does NOT mark the order PAID or deduct stock. It:
      1. Validates order exists, belongs to user, and is PENDING
      2. Resolves address (explicit address_id > user's default) and sets it
      3. Validates stock availability (reserve check only)
      4. Creates a Midtrans Snap transaction
      5. Stores payment_ref (ORDER-{id}-{ts}) and payment_status="pending"

    The order transitions to PAID only later, via the Midtrans webhook
    (handle_notification) when the gateway reports settlement.

    Args:
        order_id: Order ID to pay
        jwt_user_id: Authenticated user's ID
        address_id: Optional specific address ID (overrides default)

    Returns:
        dict {"order": Order, "snap_token": str, "redirect_url": str} on success,
        ValidationResponse on error.
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
        if address_id:
            resolved_address = Address.query.filter_by(id=address_id, user_id=user_id).first()
            if not resolved_address:
                return ValidationResponse(success=False, message="Address not found", status_code=404)
        else:
            resolved_address = Address.query.filter_by(user_id=user_id, is_default=True).first()
            if not resolved_address:
                return ValidationResponse(success=False, message="Default address is not set", status_code=400)

        # 5. Validate stock availability (no deduction here — deducted on settlement)
        order_items = Order_item.query.filter(
            Order_item.order_id == order_id,
            Order_item.deleted_at.is_(None)
        ).all()

        if not order_items:
            return ValidationResponse(success=False, message="Order has no items", status_code=400)

        item_details = []
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

            # Midtrans requires integer prices (IDR has no cents).
            item_details.append({
                "id": str(product.id),
                "price": int(round(float(product.price))),
                "quantity": item.quantity,
                "name": product.name[:50],  # Midtrans caps name length
            })

        # Add tax as its own line item so item_details sum == gross_amount.
        tax_amount = int(round(float(order.tax_amount or 0)))
        if tax_amount > 0:
            item_details.append({"id": "TAX", "price": tax_amount, "quantity": 1, "name": "Tax"})

        # Subtract discount as a negative line item if present, to keep the sum balanced.
        discount_amount = int(round(float(order.discount_amount or 0)))
        if discount_amount > 0:
            item_details.append({"id": "DISCOUNT", "price": -discount_amount, "quantity": 1, "name": "Discount"})

        gross_amount = sum(i["price"] * i["quantity"] for i in item_details)

        # 6. Build a unique payment reference for this attempt: ORDER-{id}-{ts}
        payment_ref = f"ORDER-{order.id}-{int(time.time())}"

        # 7. Look up buyer details for the customer block
        buyer = User.query.get(user_id)

        param = {
            "transaction_details": {
                "order_id": payment_ref,
                "gross_amount": gross_amount,
            },
            "item_details": item_details,
            "customer_details": {
                "first_name": buyer.username if buyer else "customer",
                "email": buyer.email if buyer else None,
                "shipping_address": {
                    "first_name": resolved_address.recipient_name,
                    "phone": resolved_address.phone,
                    "address": resolved_address.address_line,
                    "city": resolved_address.city,
                    "postal_code": resolved_address.postal_code,
                },
            },
        }

        snap = get_snap_client()
        transaction = snap.create_transaction(param)

        # 8. Persist reference + set address; order stays PENDING until webhook.
        order.address_id = resolved_address.id
        order.payment_ref = payment_ref
        order.payment_status = "pending"
        db.session.commit()

        logging.info(f"Payment initiated for order {order_id}, ref={payment_ref}, gross={gross_amount}")
        return {
            "order": order,
            "snap_token": transaction.get("token"),
            "redirect_url": transaction.get("redirect_url"),
        }

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to initiate payment for order {order_id}: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while initiating payment", status_code=500)


def _verify_signature(notification):
    """
    Verify Midtrans notification authenticity.
    signature_key == sha512(order_id + status_code + gross_amount + server_key)
    Returns True if valid.
    """
    server_key = current_app.config.get("MIDTRANS_SERVER_KEY") or ""
    order_id = notification.get("order_id", "")
    status_code = notification.get("status_code", "")
    gross_amount = notification.get("gross_amount", "")
    signature = notification.get("signature_key", "")

    raw = f"{order_id}{status_code}{gross_amount}{server_key}"
    expected = hashlib.sha512(raw.encode("utf-8")).hexdigest()
    return expected == signature


def handle_notification(notification):
    """
    Process a Midtrans payment notification (webhook).

    Verifies the signature, maps the transaction status, and — only on a
    successful settlement — deducts stock and transitions PENDING -> PAID.
    Idempotent: repeated settlement callbacks for an already-PAID order are no-ops.

    Args:
        notification: parsed JSON dict from Midtrans.

    Returns:
        ValidationResponse describing the outcome (success flag + message).
    """
    try:
        # 1. Authenticity
        if not _verify_signature(notification):
            logging.warning("Rejected Midtrans notification: invalid signature")
            return ValidationResponse(success=False, message="Invalid signature", status_code=403)

        payment_ref = notification.get("order_id")
        transaction_status = notification.get("transaction_status")
        fraud_status = notification.get("fraud_status")

        if not payment_ref:
            return ValidationResponse(success=False, message="Missing order_id", status_code=400)

        # 2. Map the reference back to our order
        order = Order.query.filter(Order.payment_ref == payment_ref).first()
        if not order:
            logging.warning(f"Midtrans notification for unknown payment_ref: {payment_ref}")
            return ValidationResponse(success=False, message="Order not found for reference", status_code=404)

        # 3. Record the gateway status regardless of outcome
        order.payment_status = transaction_status

        # 4. Success states -> settle the order (idempotent)
        is_success = (
            transaction_status == "settlement"
            or (transaction_status == "capture" and fraud_status == "accept")
        )

        if is_success:
            if order.status == OrderStatus.PAID:
                # Already settled — do not double-deduct.
                db.session.commit()
                logging.info(f"Duplicate settlement for order {order.id} ignored (already PAID)")
                return ValidationResponse(success=True, message="Order already PAID", status_code=200)

            if order.status != OrderStatus.PENDING:
                db.session.commit()
                return ValidationResponse(
                    success=False,
                    message=f"Cannot settle order in status {order.status.value}",
                    status_code=400
                )

            # Re-validate + deduct stock now that payment is confirmed.
            order_items = Order_item.query.filter(
                Order_item.order_id == order.id,
                Order_item.deleted_at.is_(None)
            ).all()

            for item in order_items:
                product = Product.query.get(item.product_id)
                if not product:
                    db.session.rollback()
                    return ValidationResponse(
                        success=False,
                        message=f"Product {item.product_id} no longer available",
                        status_code=400
                    )
                if product.stock < item.quantity:
                    db.session.rollback()
                    return ValidationResponse(
                        success=False,
                        message=f"Insufficient stock for product '{product.name}' at settlement",
                        status_code=400
                    )

            for item in order_items:
                product = Product.query.get(item.product_id)
                product.stock -= item.quantity

            order.status = OrderStatus.PAID
            db.session.commit()
            logging.info(f"Order {order.id} settled -> PAID (ref={payment_ref})")
            return ValidationResponse(success=True, message="Payment settled, order PAID", status_code=200)

        # 5. Failure/terminal states — leave stock intact, just record status.
        if transaction_status in ("deny", "cancel", "expire", "failure"):
            db.session.commit()
            logging.info(f"Order {order.id} payment {transaction_status} (ref={payment_ref})")
            return ValidationResponse(success=True, message=f"Payment {transaction_status} recorded", status_code=200)

        # 6. Pending / other — nothing to do beyond recording status.
        db.session.commit()
        return ValidationResponse(success=True, message=f"Notification recorded: {transaction_status}", status_code=200)

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to handle Midtrans notification: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred while handling notification", status_code=500)
