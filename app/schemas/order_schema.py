from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import Order, OrderStatus
from app.extensions import db


class OrderSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        load_instance = True         # Convert input directly into an Order Model object
        sqla_session = db.session
        include_fk = True            # Detect user_id (buyer)
        include_relationships = False

    # --- Input Validation & Custom Error Messages ---
    name = ma.fields.Str(required=True, error_messages={"required": "Order name is not provided."})

    # --- Items: list of {product_id, quantity} for creating an order ---
    items = ma.fields.List(
        ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Raw()),
        required=True,
        load_only=True,
        error_messages={"required": "Order items are required."}
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


class OrderUpdateSchema(ma.Schema):
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
