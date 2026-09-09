import marshmallow as ma
from app.utils.sanitizer import SanitizeMixin


# =============================================================================
# INPUT SCHEMAS
# =============================================================================

class SellerProductCreateSchema(SanitizeMixin, ma.Schema):
    """
    POST /api/v1/seller-products/  (Option B).
    Seller submits catalog fields + listing fields in one payload. The service
    find-or-creates the catalog product (dedupe by barcode) and creates the
    listing in PENDING status.
    """
    # --- Catalog fields (find-or-create) ---
    brand = ma.fields.Str(required=True, validate=ma.validate.Length(min=1),
                          error_messages={"required": "Brand is not provided."})
    name = ma.fields.Str(required=True, validate=ma.validate.Length(min=1),
                         error_messages={"required": "Product name is not provided."})
    description    = ma.fields.Str(required=False, allow_none=True, load_default=None)
    model          = ma.fields.Str(required=False, allow_none=True, load_default=None)
    color          = ma.fields.Str(required=False, allow_none=True, load_default=None)
    size           = ma.fields.Str(required=False, allow_none=True, load_default=None)
    barcode        = ma.fields.Str(required=False, allow_none=True, load_default=None,
                                   metadata={"example": "8991234567890"})
    specifications = ma.fields.Raw(required=False, allow_none=True, load_default=None)
    category_ids   = ma.fields.List(ma.fields.Int(), required=False, load_default=[],
                                    metadata={"example": [1]})

    # --- Listing fields ---
    title = ma.fields.Str(required=True, validate=ma.validate.Length(min=1),
                          error_messages={"required": "Listing title is not provided."},
                          metadata={"example": "iPhone 15 Pro Max 256GB - BNIB Garansi Resmi"})
    price = ma.fields.Decimal(
        required=True,
        validate=ma.validate.Range(min=0),
        error_messages={
            "required": "Price is not provided.",
            "invalid": "'price' must be a valid decimal number.",
            "validator_failed": "Price cannot be a negative number.",
        },
    )
    stock = ma.fields.Int(required=False, load_default=0, validate=ma.validate.Range(min=0),
                          error_messages={"validator_failed": "Stock cannot be a negative number."})
    sku = ma.fields.Str(required=False, allow_none=True, load_default=None,
                        metadata={"example": "APL-IP15PM-256"})

    # user_id: admin/superadmin may create a listing on behalf of a seller.
    user_id = ma.fields.Int(required=False, load_default=None,
                            metadata={"description": "Seller user id. Sellers: auto-assigned. Admin/Superadmin: may specify."})

    @ma.pre_load
    def strip_strings(self, data, **kwargs):
        for field in ('brand', 'name', 'description', 'model', 'color', 'size', 'barcode', 'title', 'sku'):
            if field in data and isinstance(data[field], str):
                data[field] = data[field].strip()
        return data


class SellerProductUpdateSchema(SanitizeMixin, ma.Schema):
    """
    PUT /api/v1/seller-products/<id>.
    Seller edits own listing (title/price/stock/sku, ACTIVE<->INACTIVE).
    Admin/Superadmin drive approval/suspension transitions.
    """
    title = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    price = ma.fields.Decimal(required=False, validate=ma.validate.Range(min=0))
    stock = ma.fields.Int(required=False, validate=ma.validate.Range(min=0))
    sku   = ma.fields.Str(required=False, allow_none=True)
    status = ma.fields.Str(
        required=False,
        validate=ma.validate.OneOf(
            ["PENDING", "ACTIVE", "INACTIVE", "SUSPENDED", "REJECTED"],
            error="Invalid status. Must be one of: PENDING, ACTIVE, INACTIVE, SUSPENDED, REJECTED.",
        ),
    )

    @ma.pre_load
    def strip_strings(self, data, **kwargs):
        for field in ('title', 'sku'):
            if field in data and isinstance(data[field], str):
                data[field] = data[field].strip()
        return data


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class SellerProductSchema(ma.Schema):
    """Single listing response (own listing / detail)."""
    id         = ma.fields.Int(dump_only=True)
    uuid       = ma.fields.Str(dump_only=True)
    product_id = ma.fields.Int(dump_only=True)
    seller_id  = ma.fields.Int(dump_only=True)
    title      = ma.fields.Str(dump_only=True)
    slug       = ma.fields.Str(dump_only=True)
    price      = ma.fields.Float(dump_only=True)
    stock      = ma.fields.Int(dump_only=True)
    status     = ma.fields.Str(dump_only=True)
    sku        = ma.fields.Str(dump_only=True, allow_none=True)
    images     = ma.fields.List(ma.fields.Str(), dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True, allow_none=True)


class SellerProductBrowseSchema(ma.Schema):
    """
    Storefront browse row: a listing joined to its catalog spec, tagged with the
    per-product `min_price` (window function). See seller_products_design.md.
    """
    seller_product_id = ma.fields.Int(dump_only=True)
    seller_id  = ma.fields.Int(dump_only=True)
    product_id = ma.fields.Int(dump_only=True)
    title      = ma.fields.Str(dump_only=True)
    slug       = ma.fields.Str(dump_only=True)
    price      = ma.fields.Float(dump_only=True)
    min_price  = ma.fields.Float(dump_only=True)
    stock      = ma.fields.Int(dump_only=True)
    status     = ma.fields.Str(dump_only=True)
    images     = ma.fields.List(ma.fields.Str(), dump_only=True)
    # catalog spec
    brand = ma.fields.Str(dump_only=True)
    name  = ma.fields.Str(dump_only=True)
    model = ma.fields.Str(dump_only=True, allow_none=True)
    color = ma.fields.Str(dump_only=True, allow_none=True)
    size  = ma.fields.Str(dump_only=True, allow_none=True)
