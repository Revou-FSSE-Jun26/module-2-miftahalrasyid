from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import Product
from app import db

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