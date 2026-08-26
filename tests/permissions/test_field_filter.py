"""Unit tests for RBAC field permissions — pure Python, no DB."""
from app.permissions.field_filter import get_allowed_fields, get_delete_policy


class TestGetAllowedFields:
    def test_superadmin_products_read(self):
        fields = get_allowed_fields("products", ["SUPERADMIN"], "read")
        assert "id" in fields
        assert "deleted_at" in fields
        assert "user_id" in fields

    def test_buyer_products_read(self):
        fields = get_allowed_fields("products", ["BUYER"], "read")
        assert "id" in fields
        assert "name" in fields
        assert "deleted_at" not in fields
        assert "is_active" not in fields

    def test_seller_products_create(self):
        fields = get_allowed_fields("products", ["SELLER"], "create")
        assert "name" in fields
        assert "price" in fields
        assert "user_id" not in fields

    def test_buyer_cannot_create_products(self):
        fields = get_allowed_fields("products", ["BUYER"], "create")
        assert len(fields) == 0

    def test_admin_users_update(self):
        fields = get_allowed_fields("users", ["ADMIN"], "update")
        assert "roles" in fields
        assert "is_active" in fields

    def test_buyer_users_update(self):
        fields = get_allowed_fields("users", ["BUYER"], "update")
        assert "email" in fields
        assert "password" in fields
        assert "roles" not in fields

    def test_multi_role_union(self):
        fields = get_allowed_fields("products", ["BUYER", "SELLER"], "create")
        assert "name" in fields  # from SELLER
        assert "price" in fields

    def test_unknown_table_returns_empty(self):
        fields = get_allowed_fields("nonexistent", ["ADMIN"], "read")
        assert fields == set()

    def test_unknown_role_returns_empty(self):
        fields = get_allowed_fields("products", ["UNKNOWN"], "read")
        assert fields == set()

    def test_categories_admin_create(self):
        fields = get_allowed_fields("categories", ["ADMIN"], "create")
        assert "name" in fields

    def test_categories_buyer_create_empty(self):
        fields = get_allowed_fields("categories", ["BUYER"], "create")
        assert len(fields) == 0

    def test_orders_buyer_create(self):
        fields = get_allowed_fields("orders", ["BUYER"], "create")
        assert "name" in fields

    def test_orders_seller_update(self):
        fields = get_allowed_fields("orders", ["SELLER"], "update")
        assert "status" in fields


class TestGetDeletePolicy:
    def test_superadmin_products_hard(self):
        assert get_delete_policy("products", ["SUPERADMIN"]) == "hard"

    def test_admin_products_soft(self):
        assert get_delete_policy("products", ["ADMIN"]) == "soft"

    def test_seller_products_soft(self):
        assert get_delete_policy("products", ["SELLER"]) == "soft"

    def test_buyer_products_none(self):
        assert get_delete_policy("products", ["BUYER"]) is None

    def test_superadmin_users_hard(self):
        assert get_delete_policy("users", ["SUPERADMIN"]) == "hard"

    def test_admin_users_soft(self):
        assert get_delete_policy("users", ["ADMIN"]) == "soft"

    def test_multi_role_highest_wins(self):
        assert get_delete_policy("products", ["SELLER", "SUPERADMIN"]) == "hard"

    def test_categories_admin_soft(self):
        assert get_delete_policy("categories", ["ADMIN"]) == "soft"

    def test_orders_buyer_soft(self):
        assert get_delete_policy("orders", ["BUYER"]) == "soft"

    def test_unknown_table_none(self):
        assert get_delete_policy("nonexistent", ["ADMIN"]) is None
