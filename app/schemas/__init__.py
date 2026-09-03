from .user_schema import UserSchema, UserUpdateFormSchema, UserUpdateSuccessResponseSchema, UserErrorExamples
from .product_schema import ProductSchema, ProductUpdateSchema, ProductErrorExamples
from .order_schema import OrderSchema, OrderUpdateSchema
from .order_item_schema import OrderItemSchema, OrderErrorExamples, OrderUpdateSuccessResponseSchema
from .category_schema import CategorySchema, CategoryUpdateSchema
from .profile_schema import ProfileSchema, ProfileUpdateSchema
from .address_schema import AddressSchema, AddressUpdateSchema
from .auth_schema import (
    RegisterSchema,
    LoginSchema,
    OAuthGoogleSchema,
    TokenResponseSchema,
    EmailConfirmationResponseSchema,
    AuthErrorExamples,
)
from .query_schema import (
    UserQueryArgs,
)
import marshmallow as ma
from app.utils.sanitizer import SanitizeMixin


# =============================================================================
# SHARED SCHEMAS (used across multiple endpoints)
# =============================================================================

class DeleteActionSchema(SanitizeMixin, ma.Schema):
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
    "OrderUpdateSchema",
    "OrderItemSchema",
    "OrderErrorExamples",
    "OrderUpdateSuccessResponseSchema",
    "CategorySchema",
    "CategoryUpdateSchema",
    "DeleteActionSchema",
    "ProfileSchema",
    "ProfileUpdateSchema",
    "AddressSchema",
    "AddressUpdateSchema",
    "UserUpdateFormSchema",
    "UserUpdateSuccessResponseSchema",
    "UserErrorExamples",
    "RegisterSchema",
    "LoginSchema",
    "OAuthGoogleSchema",
    "TokenResponseSchema",
    "EmailConfirmationResponseSchema",
    "AuthErrorExamples",
    "UserQueryArgs",
]
