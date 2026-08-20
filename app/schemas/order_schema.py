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
        include_relationships = True # Auto-detect Many-to-Many Product relationship (order_items)

    # --- Input Validation & Custom Error Messages ---
    name = ma.fields.Str(required=True, error_messages={"required": "Order name is not provided."})
    allowed_statuses = ", ".join([s.value for s in OrderStatus])
    status = ma.fields.Enum(
        OrderStatus,
        by_value=True,
        error_messages={"invalid": f"Invalid order status. Choose from {allowed_statuses}."}
    )
    total = ma.fields.Decimal(
        required=True,
        validate=ma.validate.Range(min=0),
        error_messages={
            "required": "Total price is not provided.",
            "invalid": "Total must be a valid decimal number.",
            "validator_failed": "Total price cannot be a negative number."
        }
    )

    id = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True)

    @ma.pre_load
    def lowercase_name(self, data, **kwargs):
        """Auto-lowercase name before validation to comply with CheckConstraint"""
        if isinstance(data, dict) and "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].lower()
        return data
