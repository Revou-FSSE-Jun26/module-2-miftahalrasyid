# =============================================================================
# TABLE-BASED RBAC FIELD PERMISSIONS
# =============================================================================
# Keyed by table name -> role -> operation -> set of allowed columns
# "delete" key: "hard" | "soft" | None
#
# This config answers: "For table X, what can role Y do with column Z?"
# =============================================================================

FIELD_PERMISSIONS = {
    "users": {
        "SUPERADMIN": {
            "create": {"email", "password", "age", "is_active", "roles"},
            "read":   {"id", "email", "age", "is_active", "roles", "username", "provider", "created_at"},
            "update": {"email", "password", "age", "is_active", "roles"},
            "delete": "hard",
        },
        "ADMIN": {
            "create": {"email", "password", "age", "is_active", "roles"},
            "read":   {"email", "age", "is_active", "roles", "username", "provider", "created_at"},
            "update": {"email", "password", "age", "is_active", "roles"},
            "delete": "soft",
        },
        "SELLER": {
            "create": set(),
            "read":   {"email", "age", "username"},
            "update": {"email", "password", "age"},
            "delete": None,
        },
        "BUYER": {
            "create": set(),
            "read":   {"email", "age", "username"},
            "update": {"email", "password", "age"},
            "delete": None,
        },
    },
    "categories": {
        "SUPERADMIN": {
            "create": {"name", "created_at", "deleted_at"},
            "read":   {"id", "name", "created_at", "deleted_at"},
            "read_list": {"name", "created_at", "deleted_at"},
            "update": {"name", "deleted_at"},
            "delete": "hard",
        },
        "ADMIN": {
            "create": {"name", "created_at", "deleted_at"},
            "read":   {"id", "name", "created_at", "deleted_at"},
            "read_list": {"name", "created_at", "deleted_at"},
            "update": {"name", "deleted_at"},
            "delete": "soft",
        },
        "SELLER": {
            "create": set(),
            "read":   {"id", "name", "created_at"},
            "read_list": {"name", "created_at"},
            "update": set(),
            "delete": None,
        },
        "BUYER": {
            "create": set(),
            "read":   {"id", "name", "created_at"},
            "read_list": {"name", "created_at"},
            "update": set(),
            "delete": None,
        },
    },
    "products": {
        "SUPERADMIN": {
            "create": {"user_id", "name", "stock", "brand", "description", "price", "is_active", "sku", "category_ids"},
            "read":   {"id", "user_id", "name", "slug", "stock", "brand", "description", "price", "created_at", "is_active", "sku", "images", "categories", "deleted_at"},
            "update": {"user_id", "name", "stock", "brand", "description", "price", "is_active", "sku", "category_ids"},
            "delete": "hard",
        },
        "ADMIN": {
            "create": {"user_id", "name", "stock", "brand", "description", "price", "is_active", "sku", "category_ids"},
            "read":   {"id", "user_id", "name", "slug", "stock", "brand", "description", "price", "created_at", "is_active", "sku", "images", "categories", "deleted_at"},
            "update": {"user_id", "name", "stock", "brand", "description", "price", "is_active", "sku", "category_ids"},
            "delete": "soft",
        },
        "SELLER": {
            "create": {"name", "stock", "brand", "description", "price", "sku", "category_ids"},
            "read":   {"id", "user_id", "name", "slug", "stock", "brand", "description", "price", "created_at", "is_active", "sku", "images", "categories"},
            "update": {"name", "stock", "brand", "description", "price", "sku", "category_ids"},
            "delete": "soft",
        },
        "BUYER": {
            "create": set(),
            "read":   {"id", "user_id", "name", "slug", "stock", "brand", "description", "price", "created_at", "sku", "images", "categories"},
            "update": set(),
            "delete": None,
        },
    },
    "orders": {
        "SUPERADMIN": {
            "create": {"name", "status", "total", "user_id"},
            "read":   {"id", "user_id", "name", "status", "total", "created_at", "deleted_at"},
            "update": {"name", "status"},
            "delete": "hard",
        },
        "ADMIN": {
            "create": {"name", "status", "total", "user_id"},
            "read":   {"id", "user_id", "name", "status", "total", "created_at", "deleted_at"},
            "update": {"name", "status"},
            "delete": "soft",
        },
        "SELLER": {
            "create": set(),
            "read":   {"id", "user_id", "name", "status", "total", "created_at"},
            "update": {"status"},
            "delete": None,
        },
        "BUYER": {
            "create": {"name"},
            "read":   {"id", "name", "status", "total", "created_at"},
            "update": set(),
            "delete": "soft",
        },
    },
    "uploads": {
        "SUPERADMIN": {
            "create": {"products"},
            "delete": "hard",
            "bypass_ownership": True,
        },
        "ADMIN": {
            "create": set(),
            "delete": "hard",
            "bypass_ownership": True,
        },
        "SELLER": {
            "create": {"products"},
            "delete": "hard",
            "bypass_ownership": False,
        },
        "BUYER": {
            "create": set(),
            "delete": None,
            "bypass_ownership": False,
        },
    },
}
