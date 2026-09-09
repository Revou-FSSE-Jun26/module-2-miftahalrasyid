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
    # --- Catalog products (spec sheet). Write = admin-curated; read = everyone. ---
    "products": {
        "SUPERADMIN": {
            "create": {"brand", "name", "description", "model", "color", "size", "barcode", "specifications", "category_ids"},
            "read":   {"id", "uuid", "brand", "name", "description", "model", "color", "size", "barcode", "specifications", "categories", "created_at", "deleted_at"},
            "update": {"brand", "name", "description", "model", "color", "size", "barcode", "specifications", "category_ids"},
            "delete": "hard",
        },
        "ADMIN": {
            "create": {"brand", "name", "description", "model", "color", "size", "barcode", "specifications", "category_ids"},
            "read":   {"id", "uuid", "brand", "name", "description", "model", "color", "size", "barcode", "specifications", "categories", "created_at", "deleted_at"},
            "update": {"brand", "name", "description", "model", "color", "size", "barcode", "specifications", "category_ids"},
            "delete": "soft",
        },
        "SELLER": {
            "create": set(),   # sellers create catalog only implicitly via seller-products (Option B)
            "read":   {"id", "uuid", "brand", "name", "description", "model", "color", "size", "barcode", "specifications", "categories", "created_at"},
            "update": set(),
            "delete": None,
        },
        "BUYER": {
            "create": set(),
            "read":   {"id", "uuid", "brand", "name", "description", "model", "color", "size", "barcode", "specifications", "categories", "created_at"},
            "update": set(),
            "delete": None,
        },
    },
    # --- Seller listings (the offer: price/stock/status/images/title). ---
    "seller_products": {
        "SUPERADMIN": {
            "create": {"user_id", "title", "price", "stock", "status", "sku"},
            "read":   {"id", "uuid", "product_id", "seller_id", "title", "slug", "price", "stock", "status", "sku", "images", "created_at", "deleted_at"},
            "update": {"title", "price", "stock", "status", "sku"},
            "delete": "hard",
        },
        "ADMIN": {
            "create": {"user_id", "title", "price", "stock", "status", "sku"},
            "read":   {"id", "uuid", "product_id", "seller_id", "title", "slug", "price", "stock", "status", "sku", "images", "created_at", "deleted_at"},
            "update": {"title", "price", "stock", "status", "sku"},
            "delete": "soft",
        },
        "SELLER": {
            "create": {"title", "price", "stock", "sku"},
            "read":   {"id", "uuid", "product_id", "seller_id", "title", "slug", "price", "stock", "status", "sku", "images", "created_at"},
            "update": {"title", "price", "stock", "sku", "status"},
            "delete": "soft",
        },
        "BUYER": {
            "create": set(),
            "read":   {"id", "product_id", "seller_id", "title", "slug", "price", "stock", "status", "images", "created_at"},
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
            "create": {"products", "seller_products"},
            "delete": "hard",
            "bypass_ownership": True,
        },
        "ADMIN": {
            "create": set(),
            "delete": "hard",
            "bypass_ownership": True,
        },
        "SELLER": {
            "create": {"products", "seller_products"},
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
