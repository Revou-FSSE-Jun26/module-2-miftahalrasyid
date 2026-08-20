from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import Category
from app.extensions import db


class CategorySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        load_instance = True         # Convert input directly into a Category Model object
        sqla_session = db.session
        include_relationships = True # Auto-detect Many-to-Many Product relationship (category_items)

    # --- Input Validation & Custom Error Messages ---
    name = ma.fields.Str(required=True, error_messages={"required": "Category name is not provided."})

    id = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True)

    @ma.pre_load
    def lowercase_name(self, data, **kwargs):
        """Auto-lowercase name before validation to comply with CheckConstraint"""
        if isinstance(data, dict) and "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].lower()
        return data
