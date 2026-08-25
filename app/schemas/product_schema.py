from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import Product
from app.extensions import db
from app.utils.sanitizer import SanitizeMixin


class ProductSchema(SanitizeMixin, SQLAlchemyAutoSchema):
    class Meta:
        model                 = Product
        load_instance         = True        # Convert input directly into a Product Model object
        sqla_session          = db.session
        include_fk            = True        # Include foreign keys like user_id
        include_relationships = False       # Don't auto-include relationships
        exclude               = ('seller', 'categories', 'uuid')  # Exclude from API input/output

    # --- Required fields ---
    name        = ma.fields.Str(
        required=True, 
        validate       = ma.validate.Length(min=1, error="Product name cannot be empty."),
        error_messages={"required": "Product name is not provided."}
    )
    brand       = ma.fields.Str(required=True, error_messages={"required": "Brand name is not provided."})
    description = ma.fields.Str(required=True, error_messages={"required": "Description is not provided."})
    price       = ma.fields.Decimal(
        required       = True,
        validate       = ma.validate.Range(min=0),
        error_messages = {
            "required"        : "Price is not provided.",
            "invalid"         : "'price' must be a valid decimal number.",
            "validator_failed": "Price cannot be a negative number."
        }
    )

    # --- Optional fields ---
    stock = ma.fields.Int(
        required       = False,
        load_default   = 0,
        validate       = ma.validate.Range(min=0),
        error_messages = {
            "invalid"         : "'stock' must be a valid number.",
            "validator_failed": "Stock cannot be a negative number."
        }
    )
    sku = ma.fields.Str(
        required     = False,
        load_default = None,
        allow_none   = True,
        metadata     = {"example": "SKU-LAPTOP-001"}
    )

    # Category IDs: Optional list of category IDs to link to the product.
    # This field is NOT on the model — we intercept it in pre_load so it never
    # reaches the Product() constructor. The route handler reads it back from
    # product_instance._category_ids_input after deserialization.
    category_ids = ma.fields.List(
        ma.fields.Int(),
        required     = False,
        load_default = [],
        load_only    = True,
        metadata     = {"example": [1, 2]}
    )
    is_active  = ma.fields.Bool(
        required     = False,
        load_default = True
    )

    user_id    = ma.fields.Int(
        load_only    = True,
        required     = False,
        load_default = True
    )
    
    # --- dump_only: server-generated, never in request body ---
    id         = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True)

    @ma.pre_load
    def pop_category_ids(self, data, **kwargs):
        """
        Remove category_ids from the payload BEFORE Marshmallow-SQLAlchemy
        tries to pass it into Product(). The route handler will read
        category_ids directly from the raw request JSON instead.
        """
        for field in ('name', 'brand', 'description', 'sku'):
            if field in data and isinstance(data[field], str):
                data[field] = data[field].strip()
        data.pop('category_ids', [])
        return data
    
class ProductUpdateSchema(SanitizeMixin, SQLAlchemyAutoSchema):
    class Meta:
        model                 = Product
        load_instance         = False       # Return dict, not model instance
        sqla_session          = db.session
        include_fk            = True
        include_relationships = False
        exclude               = ('seller', 'categories', 'uuid')

    # --- All fields optional for partial update ---
    name        = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    brand       = ma.fields.Str(required=False)
    description = ma.fields.Str(required=False)
    price       = ma.fields.Decimal(required=False, validate=ma.validate.Range(min=0))
    stock       = ma.fields.Int(required=False, validate=ma.validate.Range(min=0))
    sku         = ma.fields.Str(required=False, allow_none=True)
    is_active   = ma.fields.Bool(required=False)
    category_ids = ma.fields.List(
        ma.fields.Int(),
        required=False,
        load_only=True
    )

    # --- Never accept from client ---
    id         = ma.fields.Int(dump_only=True)
    user_id    = ma.fields.Int(required=False)
    created_at = ma.fields.DateTime(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True)

    @ma.pre_load
    def strip_strings(self, data, **kwargs):
        for field in ('name', 'brand', 'description', 'sku'):
            if field in data and isinstance(data[field], str):
                data[field] = data[field].strip()
        return data


class ProductErrorExamples:
    """Reusable error response examples for user routes."""
    # --- 401: Unauthorized (JWT) ---
    TOKEN_MISSING = {
        "summary": "Authorization Token Missing",
        "value": {
            "code": 401,
            "errors": "Missing authorization token.",
            "status": "Unauthorized"
        }
    }

    TOKEN_EXPIRED = {
        "summary": "Authorization Token Expired",
        "value": {
            "code": 401,
            "errors": "Token has expired.",
            "status": "Unauthorized"
        }
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