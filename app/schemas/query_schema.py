"""
Reusable query-parameter schemas for GET list endpoints.

These schemas are used with `@blueprint.arguments(Schema, location="query")`
so the parameters appear in Swagger UI and are validated by Marshmallow before
reaching the route/service.

RBAC note:
    Privileged filters (e.g. filtering users by `role` / `is_active`) are declared
    here for documentation, but they are only *honored* by the service layer for
    admin/superadmin callers. The service silently ignores them for lower roles,
    so a buyer/seller cannot use them to enumerate data they shouldn't see.
"""
import marshmallow as ma
from app.models import UserRole
from app.models.order_model import OrderStatus
from app.utils.sanitizer import SanitizeMixin


class PaginationQueryArgs(ma.Schema):
    """Base pagination params shared by every list endpoint."""
    page = ma.fields.Int(
        load_default=1,
        validate=ma.validate.Range(min=1),
        metadata={"description": "Page number (1-based).", "example": 1},
    )
    per_page = ma.fields.Int(
        load_default=10,
        validate=ma.validate.Range(min=1, max=30),
        metadata={"description": "Items per page (max 30).", "example": 10},
    )


class ProductQueryArgs(SanitizeMixin, PaginationQueryArgs):
    """Filtering/sorting for GET /products/ and category product listings.
    SanitizeMixin strips HTML from the free-text `search` field (XSS defense).
    """
    search = ma.fields.Str(
        load_default=None,
        metadata={"description": "Case-insensitive match on product name.", "example": "mouse"},
    )
    category_id = ma.fields.Int(
        load_default=None,
        metadata={"description": "Only products linked to this category id.", "example": 1},
    )
    min_price = ma.fields.Decimal(
        load_default=None,
        validate=ma.validate.Range(min=0),
        metadata={"description": "Minimum price (inclusive).", "example": 10000},
    )
    max_price = ma.fields.Decimal(
        load_default=None,
        validate=ma.validate.Range(min=0),
        metadata={"description": "Maximum price (inclusive).", "example": 5000000},
    )
    sort = ma.fields.Str(
        load_default=None,
        validate=ma.validate.OneOf(
            ["price", "-price", "name", "-name", "created_at", "-created_at"]
        ),
        metadata={
            "description": "Sort field. Prefix with '-' for descending.",
            "example": "-price",
        },
    )


class CategoryQueryArgs(SanitizeMixin, PaginationQueryArgs):
    """Filtering/sorting for GET /categories/.
    SanitizeMixin strips HTML from the free-text `search` field (XSS defense).
    """
    search = ma.fields.Str(
        load_default=None,
        metadata={"description": "Case-insensitive match on category name.", "example": "electronic"},
    )
    sort = ma.fields.Str(
        load_default=None,
        validate=ma.validate.OneOf(["name", "-name", "created_at", "-created_at"]),
        metadata={"description": "Sort field. Prefix with '-' for descending.", "example": "name"},
    )


class OrderQueryArgs(PaginationQueryArgs):
    """
    Filtering/sorting for GET /orders/.
    Ownership scoping (buyer=own, seller=their products, admin=all) is enforced
    in the service and is NOT overridable via query params.
    """
    status = ma.fields.Str(
        load_default=None,
        validate=ma.validate.OneOf([s.value for s in OrderStatus]),
        metadata={"description": "Filter by order status.", "example": "PAID"},
    )
    sort = ma.fields.Str(
        load_default=None,
        validate=ma.validate.OneOf(["total", "-total", "created_at", "-created_at"]),
        metadata={"description": "Sort field. Prefix with '-' for descending.", "example": "-created_at"},
    )


class UserQueryArgs(SanitizeMixin, PaginationQueryArgs):
    """
    Filtering for GET /users/.
    `role` and `is_active` are privileged filters: honored only for
    admin/superadmin callers (enforced in the service layer).
    SanitizeMixin strips HTML from the free-text `search` field (XSS defense).
    """
    search = ma.fields.Str(
        load_default=None,
        metadata={"description": "Case-insensitive match on username or email.", "example": "budi"},
    )
    role = ma.fields.Str(
        load_default=None,
        validate=ma.validate.OneOf([r.value for r in UserRole]),
        metadata={"description": "Filter by role (admin/superadmin only).", "example": "SELLER"},
    )
    is_active = ma.fields.Bool(
        load_default=None,
        metadata={"description": "Filter by active flag (admin/superadmin only).", "example": True},
    )
    sort = ma.fields.Str(
        load_default=None,
        validate=ma.validate.OneOf(["username", "-username", "created_at", "-created_at"]),
        metadata={"description": "Sort field. Prefix with '-' for descending.", "example": "username"},
    )


class AdminProductQueryArgs(ProductQueryArgs):
    """
    Filtering for admin product listings (GET /admin/products,
    GET /admin/categories/<id>/products) which include inactive/soft-deleted.
    """
    is_active = ma.fields.Bool(
        load_default=None,
        metadata={"description": "Filter by active flag.", "example": False},
    )
    include_deleted = ma.fields.Bool(
        load_default=True,
        metadata={
            "description": "Include soft-deleted products (default true for admin view).",
            "example": True,
        },
    )


class AdminOrderQueryArgs(PaginationQueryArgs):
    """Filtering for GET /admin/users/<id>/orders."""
    status = ma.fields.Str(
        load_default=None,
        validate=ma.validate.OneOf([s.value for s in OrderStatus]),
        metadata={"description": "Filter by order status.", "example": "PAID"},
    )
    sort = ma.fields.Str(
        load_default=None,
        validate=ma.validate.OneOf(["total", "-total", "created_at", "-created_at"]),
        metadata={"description": "Sort field. Prefix with '-' for descending.", "example": "-created_at"},
    )
