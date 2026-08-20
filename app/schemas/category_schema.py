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
        """Strip whitespace and auto-lowercase name before validation"""
        if isinstance(data, dict) and "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].strip().lower()
        return data


class CategoryUpdateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        load_instance = False        # Return dict, not model instance
        sqla_session = db.session
        include_relationships = False

    # --- All fields optional for partial update ---
    name = ma.fields.Str(required=False, validate=ma.validate.Length(min=1, error="Category name cannot be empty."))

    # --- Never accept from client ---
    id = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True)

    @ma.pre_load
    def lowercase_name(self, data, **kwargs):
        """Strip whitespace and auto-lowercase name before validation"""
        if isinstance(data, dict) and "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].strip().lower()
        return data
