# app/schemas.py
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import User,Product,Order,OrderStatus,Category
from app import db

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True       # Smorest otomatis membuatkan objek Model dari input
        sqla_session = db.session   # Menggunakan session database Anda
        include_fk = True          # Otomatis mendeteksi Foreign Key jika

        # --- KUSTOMISASI PESAN ERROR UNTUK FIELD WAJIB ---
    
    email = ma.fields.Email(
        required=True,
        error_messages={
            "required": "Email is not provided.",
            "invalid": "Email format is wrong."
        }
    )
    
    age = ma.fields.Int(
        required=True,
        error_messages={
            "required": "Age is not provided.",
            "invalid": "'age' must be a valid number."
        }
    )
    
    password = ma.fields.Str(
        required=True, 
        load_only=True,
        error_messages={
            "required": "Password is not provided."
        }
    )

class ProductSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        load_instance = True         # Mengubah input langsung jadi objek Model Product
        sqla_session = db.session
        include_fk = True            # Wajib terpasang untuk mendeteksi user_id (Seller)
        include_relationships = True # Otomatis mendeteksi relasi Many-to-Many Category

    # --- Kustomisasi Validasi Input & Pesan Error ---
    name = ma.fields.Str(required=True, error_messages={"required": "Product name is not provided."})
    brand = ma.fields.Str(required=True, error_messages={"required": "Brand name is not provided."})
    
    quantity = ma.fields.Int(
        required=True,
        validate=ma.validate.Range(min=0),
        error_messages={
            "required": "Quantity is not provided.",
            "invalid": "Quantity must be a valid number.",
            "validator_failed": "Quantity cannot be a negative number."
        }
    )
    price = ma.fields.Decimal(
        required=True,
        validate=ma.validate.Range(min=0),
        error_messages={
            "required": "Price is not provided.",
            "invalid": "Price must be a valid decimal number.",
            "validator_failed": "Price cannot be a negative number."
        }
    )

    id = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)

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

class CategorySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        load_instance = True         # Mengubah input langsung jadi objek Model Category
        sqla_session = db.session
        include_relationships = True # Otomatis mendeteksi relasi Many-to-Many Product (category_items)

    # --- Kustomisasi Validasi Input & Pesan Error ---
    name = ma.fields.Str(required=True, error_messages={"required": "Category name is not provided."})

    id = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)

    @ma.pre_load
    def lowercase_name(self, data, **kwargs):
        """Otomatis lowercase data sebelum divalidasi agar aman dari CheckConstraint"""
        if isinstance(data, dict) and "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].lower()
        return data