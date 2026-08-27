import marshmallow as ma
from app.utils.sanitizer import SanitizeMixin


class PaymentRequestSchema(SanitizeMixin, ma.Schema):
    """
    Schema for POST /api/v1/payment.
    order_id is required. address_id is optional (falls back to user's default address).
    """
    order_id = ma.fields.Int(
        required=True,
        error_messages={"required": "order_id is required."},
        metadata={"example": 1, "description": "ID of the PENDING order to pay"}
    )
    address_id = ma.fields.Int(
        required=False,
        load_default=None,
        metadata={"example": 2, "description": "Optional address ID. If omitted, uses user's default address."}
    )


class PaymentOrderDataSchema(ma.Schema):
    """Nested schema for the order data in payment response."""
    id = ma.fields.Int(metadata={"example": 1})
    user_id = ma.fields.Int(metadata={"example": 5})
    address_id = ma.fields.Int(metadata={"example": 2})
    name = ma.fields.Str(metadata={"example": "my order"})
    status = ma.fields.Str(metadata={"example": "PAID"})
    subtotal = ma.fields.Float(metadata={"example": 200.00})
    discount_percent = ma.fields.Float(metadata={"example": 0})
    discount_amount = ma.fields.Float(metadata={"example": 0})
    tax_percent = ma.fields.Float(metadata={"example": 11})
    tax_amount = ma.fields.Float(metadata={"example": 22.00})
    total = ma.fields.Float(metadata={"example": 222.00})
    created_at = ma.fields.Str(metadata={"example": "2026-08-27T10:00:00+00:00"})
    items = ma.fields.List(ma.fields.Dict(), metadata={"example": [{"id": 1, "product_id": 3, "quantity": 2, "compound_price": 200.00}]})


class PaymentResponseSchema(ma.Schema):
    """Response schema for successful payment (200)."""
    success = ma.fields.Bool(metadata={"example": True})
    message = ma.fields.Str(metadata={"example": "Payment processed successfully"})
    data = ma.fields.Nested(PaymentOrderDataSchema)


class PaymentErrorExamples:
    """Reusable error response examples for payment route Swagger docs."""

    NO_DEFAULT_ADDRESS = {
        "summary": "No Default Address Set",
        "value": {
            "code": 400,
            "message": "Default address is not set",
            "status": "Bad Request"
        }
    }

    INSUFFICIENT_STOCK = {
        "summary": "Insufficient Stock",
        "value": {
            "code": 400,
            "message": "Insufficient stock for product 'Widget'. Available: 2, required: 5",
            "status": "Bad Request"
        }
    }

    ORDER_NOT_PENDING = {
        "summary": "Order Not In PENDING Status",
        "value": {
            "code": 400,
            "message": "Only PENDING orders can be paid. Current status: PAID",
            "status": "Bad Request"
        }
    }

    PRODUCT_UNAVAILABLE = {
        "summary": "Product No Longer Available",
        "value": {
            "code": 400,
            "message": "Product with id '5' is no longer available",
            "status": "Bad Request"
        }
    }

    ORDER_NOT_FOUND = {
        "summary": "Order Not Found",
        "value": {
            "code": 404,
            "message": "Order not found",
            "status": "Not Found"
        }
    }

    ADDRESS_NOT_FOUND = {
        "summary": "Address Not Found",
        "value": {
            "code": 404,
            "message": "Address not found",
            "status": "Not Found"
        }
    }

    UNAUTHORIZED = {
        "summary": "Unauthorized To Pay",
        "value": {
            "code": 403,
            "message": "Unauthorized to pay for this order",
            "status": "Forbidden"
        }
    }

    ORDER_ID_MISSING = {
        "summary": "Order ID Not Provided",
        "value": {
            "code": 422,
            "errors": {"json": {"order_id": ["order_id is required."]}},
            "status": "Unprocessable Entity"
        }
    }

