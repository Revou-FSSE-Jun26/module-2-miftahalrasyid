from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models.order_items_model import Order_item
from app.extensions import db


class OrderItemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Order_item
        load_instance = True
        sqla_session = db.session
        include_fk = True

    # --- dump_only: server-generated, not from client input ---
    id = ma.fields.Int(dump_only=True)
    order_id = ma.fields.Int(dump_only=True)
    compound_price = ma.fields.Decimal(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True)

    # --- client input: only these come from the request ---
    product_id = ma.fields.Int(
        required=True,
        error_messages={"required": "Product ID is required."}
    )
    quantity = ma.fields.Int(
        required=True,
        validate=ma.validate.Range(min=1, error="Quantity must be at least 1."),
        error_messages={
            "required": "Quantity is required.",
            "invalid": "'quantity' must be a valid number."
        }
    )


# =============================================================================
# DATA HOLDER CLASS - Error Response Examples for Swagger Examples Dropdown
# =============================================================================

class OrderErrorExamples:
    """Reusable error response examples for order routes."""

    # --- 422: JSON Validation Failed ---
    PRODUCT_ID_MISSING = {
        "summary": "Product ID Not Provided",
        "value": {
            "code": 422,
            "errors": {"json": {"product_id": ["Product ID is required."]}},
            "status": "Unprocessable Entity"
        }
    }

    QUANTITY_MISSING = {
        "summary": "Quantity Not Provided",
        "value": {
            "code": 422,
            "errors": {"json": {"quantity": ["Quantity is required."]}},
            "status": "Unprocessable Entity"
        }
    }

    QUANTITY_INVALID = {
        "summary": "Quantity Is Not a Valid Number",
        "value": {
            "code": 422,
            "errors": {"json": {"quantity": ["'quantity' must be a valid number."]}},
            "status": "Unprocessable Entity"
        }
    }

    QUANTITY_TOO_LOW = {
        "summary": "Quantity Less Than 1",
        "value": {
            "code": 422,
            "errors": {"json": {"quantity": ["Quantity must be at least 1."]}},
            "status": "Unprocessable Entity"
        }
    }

    ORDER_NAME_MISSING = {
        "summary": "Order Name Not Provided",
        "value": {
            "code": 422,
            "errors": {"json": {"name": ["Order name is not provided."]}},
            "status": "Unprocessable Entity"
        }
    }

    # --- 400: Business Logic Failed ---
    PRODUCT_NOT_FOUND = {
        "summary": "Product ID Not Found",
        "value": {
            "code": 400,
            "errors": "Product with id '99' is not found.",
            "status": "Bad Request"
        }
    }

    DUPLICATE_PRODUCT_IN_ORDER = {
        "summary": "Product Already Exists in Order",
        "value": {
            "code": 400,
            "errors": "Product already exists in this order.",
            "status": "Bad Request"
        }
    }

    # --- 404: Order Not Found ---
    ORDER_NOT_FOUND = {
        "summary": "Order Not Found",
        "value": {
            "code": 404,
            "errors": "Order not found.",
            "status": "Not Found"
        }
    }


# =============================================================================
# SUCCESS RESPONSE SCHEMA (200) - Update/Create Order Items
# =============================================================================

class OrderUpdateFieldsContainerSchema(ma.Schema):
    order = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["order has been created"]})
    items = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["item has been added"]})
    status = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["status has updated"]})


class OrderUpdateSuccessResponseSchema(ma.Schema):
    form = ma.fields.Nested(OrderUpdateFieldsContainerSchema, required=True)
