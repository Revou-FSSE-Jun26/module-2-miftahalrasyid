from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import Order,OrderStatus
from app import db

class OrderSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        load_instance = True         # Mengubah input langsung jadi objek Model Order
        sqla_session = db.session
        include_fk = True            # Mendeteksi user_id pembeli
        include_relationships = True # Otomatis mendeteksi relasi Many-to-Many Product (order_items)

    # --- Kustomisasi Validasi Input & Pesan Error ---
    name = ma.fields.Str(required=True, error_messages={"required": "Order name is not provided."})
    allowed_statuses = ", ".join([s.value for s in OrderStatus])
    OrderStatus._member_map_
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

    @ma.pre_load
    def lowercase_name(self, data, **kwargs):
        """Otomatis lowercase data sebelum divalidasi agar aman dari CheckConstraint"""
        if isinstance(data, dict) and "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].lower()
        return data
