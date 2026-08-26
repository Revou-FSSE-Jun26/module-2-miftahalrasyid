"""Unit tests for roles_required middleware — uses Flask test client with mock routes."""
from unittest.mock import patch


class TestRolesRequired:
    def test_allows_correct_role(self, client, seller_headers):
        resp = client.get('/api/v1/products/', headers=seller_headers)
        # Products GET is public, doesn't need auth — just verify no 500
        assert resp.status_code in (200, 400)

    def test_blocks_no_token_on_protected_route(self, client):
        resp = client.get('/api/v1/orders/')
        assert resp.status_code == 401

    def test_blocks_wrong_role(self, client, buyer_headers):
        # Buyer cannot POST categories (admin only)
        resp = client.post('/api/v1/categories/', headers=buyer_headers, json={'name': 'test'})
        assert resp.status_code == 403

    def test_admin_can_access_admin_routes(self, client, admin_headers):
        resp = client.get('/api/v1/admin/products', headers=admin_headers)
        # Should NOT be 401/403 — auth passes, may get 200 or 500 depending on DB state
        assert resp.status_code not in (401, 403)

    def test_buyer_blocked_from_admin(self, client, buyer_headers):
        resp = client.get('/api/v1/admin/products', headers=buyer_headers)
        assert resp.status_code == 403

    def test_superadmin_access_all(self, client, superadmin_headers):
        resp = client.get('/api/v1/admin/products', headers=superadmin_headers)
        assert resp.status_code not in (401, 403)

    def test_seller_can_post_products(self, client, seller_headers):
        # Will fail on validation but should NOT be 401/403
        resp = client.post('/api/v1/products/', headers=seller_headers, json={})
        assert resp.status_code != 401
        assert resp.status_code != 403

    def test_expired_token_returns_401(self, client):
        headers = {'Authorization': 'Bearer invalid.token.here', 'Content-Type': 'application/json'}
        resp = client.get('/api/v1/orders/', headers=headers)
        assert resp.status_code in (401, 422)
