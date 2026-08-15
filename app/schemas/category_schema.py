from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import Category
from app import db




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