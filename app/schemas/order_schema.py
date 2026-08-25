from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import Order, OrderStatus
from app.extensions import db
from app.utils.sanitizer import SanitizeMixin


class OrderItemInputSchema(ma.Schema):
    """Schema for a single item in the order creation request."""
    product_id = ma.fields.Int(
        required=True,
        error_messages={"required": "Product ID is required."},
        metadata={"example": 1}
    )
    quantity = ma.fields.Int(
        required=True,
        validate=ma.validate.Range(min=1, error="Quantity must be at least 1."),
        error_messages={
            "required": "Quantity is required.",
            "invalid": "'quantity' must be a valid number."
        },
        metadata={"example": 2}
    )


class OrderSchema(SanitizeMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        load_instance = True
        sqla_session = db.session
        include_fk = True
        include_relationships = False

    # --- Input Validation ---
    name = ma.fields.Str(
        required=True,
        error_messages={"required": "Order name is not provided."},
        metadata={"example": "my weekend order"}
    )

    # --- Items: list of {product_id, quantity} for creating an order ---
    items = ma.fields.List(
        ma.fields.Nested(OrderItemInputSchema),
        required=True,
        load_only=True,
        error_messages={"required": "Order items are required."},
        metadata={"example": [{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]}
    )

    # --- dump_only: server-generated ---
    id = ma.fields.Int(dump_only=True)
    user_id = ma.fields.Int(dump_only=True)
    status = ma.fields.Str(dump_only=True)
    total = ma.fields.Decimal(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True)

    @ma.pre_load
    def lowercase_name(self, data, **kwargs):
        """Strip whitespace and auto-lowercase name before validation"""
        if isinstance(data, dict) and "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].strip().lower()
        return data


class OrderUpdateSchema(SanitizeMixin, ma.Schema):
    """Schema for updating an order (status transitions by seller/admin/superadmin)."""
    status = ma.fields.Str(
        required=False,
        validate=ma.validate.OneOf(
            [s.value for s in OrderStatus],
            error="Invalid order status. Choose from: {choices}."
        ),
        metadata={"example": "COMPLETED"}
    )
    name = ma.fields.Str(
        required=False,
        validate=ma.validate.Length(min=1, error="Order name cannot be empty.")
    )

    @ma.pre_load
    def strip_and_upper(self, data, **kwargs):
        if isinstance(data, dict):
            if "name" in data and isinstance(data["name"], str):
                data["name"] = data["name"].strip().lower()
            if "status" in data and isinstance(data["status"], str):
                data["status"] = data["status"].strip().upper()
        return data
