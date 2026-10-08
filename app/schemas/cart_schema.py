import marshmallow as ma
from app.utils.sanitizer import SanitizeMixin
from app.schemas.query_schema import PaginationQueryArgs


class CartItemAddSchema(SanitizeMixin, ma.Schema):
    """Body for POST /cart/items — add a seller listing to the cart.

    If the listing is already in the cart, the service bumps its quantity
    (see UNIQUE(user_id, seller_product_id) on cart_items).
    """
    seller_product_id = ma.fields.Int(
        required=True,
        error_messages={"required": "Seller product ID is required."},
        metadata={"example": 1},
    )
    quantity = ma.fields.Int(
        load_default=1,
        validate=ma.validate.Range(min=1, error="Quantity must be at least 1."),
        error_messages={"invalid": "'quantity' must be a valid number."},
        metadata={"example": 2},
    )


class CartItemUpdateSchema(SanitizeMixin, ma.Schema):
    """Body for PATCH /cart/items/<id> — set an absolute quantity for a line."""
    quantity = ma.fields.Int(
        required=True,
        validate=ma.validate.Range(min=1, error="Quantity must be at least 1."),
        error_messages={
            "required": "Quantity is required.",
            "invalid": "'quantity' must be a valid number.",
        },
        metadata={"example": 3},
    )


class CartItemSchema(ma.Schema):
    """Response shape for a single cart line (enriched with live listing data)."""
    id                = ma.fields.Int(dump_only=True)
    seller_product_id = ma.fields.Int(dump_only=True)
    product_id        = ma.fields.Int(dump_only=True)
    title             = ma.fields.Str(dump_only=True)
    price             = ma.fields.Float(dump_only=True)
    quantity          = ma.fields.Int(dump_only=True)
    line_total        = ma.fields.Float(dump_only=True)
    stock             = ma.fields.Int(dump_only=True)
    available         = ma.fields.Bool(dump_only=True)
    images            = ma.fields.List(ma.fields.Str(), dump_only=True)
    created_at        = ma.fields.DateTime(dump_only=True)
    updated_at        = ma.fields.DateTime(dump_only=True)


class CartQueryArgs(PaginationQueryArgs):
    """Pagination for GET /cart. Cart is ownership-scoped in the service."""
    pass
