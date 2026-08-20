from .user_schema import UserSchema, UserUpdateFormSchema, UserUpdateSuccessResponseSchema, UserErrorExamples
from .product_schema import ProductSchema, ProductUpdateSchema, ProductErrorExamples
from .order_schema import OrderSchema
from .order_item_schema import OrderItemSchema, OrderErrorExamples, OrderUpdateSuccessResponseSchema
from .category_schema import CategorySchema, CategoryUpdateSchema
from .auth_schema import (
    RegisterSchema,
    LoginSchema,
    OAuthGoogleSchema,
    TokenResponseSchema,
    EmailConfirmationResponseSchema,
    AuthErrorExamples,
)
import marshmallow as ma


# =============================================================================
# SHARED SCHEMAS (used across multiple endpoints)
# =============================================================================

class DeleteActionSchema(ma.Schema):
    """
    Shared schema for DELETE requests.
    Optional body: {"action": "hard"} for superadmin hard delete.
    Default behavior (no body or action omitted) = soft delete.
    """
    action = ma.fields.Str(
        required=False,
        load_default="soft",
        validate=ma.validate.OneOf(["soft", "hard"]),
        metadata={"example": "hard", "description": "Delete mode: 'soft' (default) or 'hard' (superadmin only)"}
    )

__all__ = [
    "UserSchema",
    "ProductSchema",
    "ProductUpdateSchema",
    "ProductErrorExamples",
    "OrderSchema",
    "OrderItemSchema",
    "OrderErrorExamples",
    "OrderUpdateSuccessResponseSchema",
    "CategorySchema",
    "CategoryUpdateSchema",
    "DeleteActionSchema",
    "UserUpdateFormSchema",
    "UserUpdateSuccessResponseSchema",
    "UserErrorExamples",
    "RegisterSchema",
    "LoginSchema",
    "OAuthGoogleSchema",
    "TokenResponseSchema",
    "EmailConfirmationResponseSchema",
    "AuthErrorExamples",
]
