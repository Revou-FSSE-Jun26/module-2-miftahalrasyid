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
}
