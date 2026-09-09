from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import Product
from app.extensions import db
from app.utils.sanitizer import SanitizeMixin


class ProductSchema(SanitizeMixin, SQLAlchemyAutoSchema):
    """
    Catalog product (spec sheet). Admin-managed. No price/stock/status/owner —
    those live on SellerProduct. See seller_products_design.md.
    """
    class Meta:
        model                 = Product
        load_instance         = True
        sqla_session          = db.session
        include_fk            = True
        include_relationships = False
        exclude               = ('categories', 'uuid', 'deleted_at')

    # --- Required fields ---
    brand = ma.fields.Str(
        required=True,
        validate=ma.validate.Length(min=1, error="Brand cannot be empty."),
        error_messages={"required": "Brand name is not provided."}
    )
    name = ma.fields.Str(
        required=True,
        validate=ma.validate.Length(min=1, error="Product name cannot be empty."),
        error_messages={"required": "Product name is not provided."}
    )

    # --- Optional catalog spec fields ---
    description    = ma.fields.Str(required=False, allow_none=True, load_default=None)
    model          = ma.fields.Str(required=False, allow_none=True, load_default=None)
    color          = ma.fields.Str(required=False, allow_none=True, load_default=None)
    size           = ma.fields.Str(required=False, allow_none=True, load_default=None)
    barcode        = ma.fields.Str(required=False, allow_none=True, load_default=None,
                                   metadata={"example": "8991234567890"})
    specifications = ma.fields.Raw(required=False, allow_none=True, load_default=None,
                                   metadata={"example": {"ram": "16GB", "cpu": "M3"}})

    # Category IDs: optional list to link categories (intercepted in pre_load).
    category_ids = ma.fields.List(
        ma.fields.Int(),
        required=False,
        load_default=[],
        load_only=True,
        metadata={"example": [1, 2]}
    )

    # --- dump_only: server-generated ---
    id         = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)

    @ma.pre_load
    def pop_category_ids(self, data, **kwargs):
        for field in ('name', 'brand', 'description', 'model', 'color', 'size', 'barcode'):
            if field in data and isinstance(data[field], str):
                data[field] = data[field].strip()
        data.pop('category_ids', [])
        return data


class ProductUpdateSchema(SanitizeMixin, SQLAlchemyAutoSchema):
    """Partial update of a catalog product (admin only)."""
    class Meta:
        model                 = Product
        load_instance         = False
        sqla_session          = db.session
        include_fk            = True
        include_relationships = False
        exclude               = ('categories', 'uuid')

    brand          = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    name           = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    description    = ma.fields.Str(required=False, allow_none=True)
    model          = ma.fields.Str(required=False, allow_none=True)
    color          = ma.fields.Str(required=False, allow_none=True)
    size           = ma.fields.Str(required=False, allow_none=True)
    barcode        = ma.fields.Str(required=False, allow_none=True)
    specifications = ma.fields.Raw(required=False, allow_none=True)
    category_ids   = ma.fields.List(ma.fields.Int(), required=False, load_only=True)

    id         = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True)

    @ma.pre_load
    def strip_strings(self, data, **kwargs):
        for field in ('name', 'brand', 'description', 'model', 'color', 'size', 'barcode'):
            if field in data and isinstance(data[field], str):
                data[field] = data[field].strip()
        return data


class ProductErrorExamples:
    """Reusable error response examples for product routes."""
    TOKEN_MISSING = {
        "summary": "Authorization Token Missing",
        "value": {"code": 401, "errors": "Missing authorization token.", "status": "Unauthorized"}
    }
    TOKEN_EXPIRED = {
        "summary": "Authorization Token Expired",
        "value": {"code": 401, "errors": "Token has expired.", "status": "Unauthorized"}
    }
    RESPONSES_POST_PRODUCT = {
        "401": {
            "description": "Authentication Required",
            "content": {
                "application/json": {
                    "examples": {
                        "TokenMissing": TOKEN_MISSING,
                        "TokenExpired": TOKEN_EXPIRED,
                    }
                }
            }
        },
    }
