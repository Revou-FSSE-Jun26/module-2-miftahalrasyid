"""Route tests for categories — mock service layer."""
from unittest.mock import patch, MagicMock
from app.services import ValidationResponse


class TestGetCategories:
    @patch('app.routes.v1.category_routes_v1.get_all_categories')
    def test_success(self, mock_svc, client):
        mock_cat = MagicMock()
        mock_cat.__dict__ = {'name': 'electronics', 'created_at': '2024-01-01', '_sa': None}
        mock_svc.return_value = {'items': [mock_cat], 'page': 1, 'per_page': 10, 'total': 1, 'pages': 1, 'count': 1}
        resp = client.get('/api/v1/categories/')
        assert resp.status_code == 200

    @patch('app.routes.v1.category_routes_v1.get_all_categories')
    def test_failure(self, mock_svc, client):
        mock_svc.return_value = None
        resp = client.get('/api/v1/categories/')
        assert resp.status_code == 400


class TestPostCategory:
    def test_no_auth(self, client):
        resp = client.post('/api/v1/categories/', json={'name': 'test'})
        assert resp.status_code == 401

    def test_buyer_forbidden(self, client, buyer_headers):
        resp = client.post('/api/v1/categories/', json={'name': 'test'}, headers=buyer_headers)
        assert resp.status_code == 403

    def test_seller_forbidden(self, client, seller_headers):
        resp = client.post('/api/v1/categories/', json={'name': 'test'}, headers=seller_headers)
        assert resp.status_code == 403


class TestGetCategoryById:
    @patch('app.routes.v1.category_routes_v1.get_category_by_id')
    def test_not_found(self, mock_svc, client):
        mock_svc.return_value = None
        resp = client.get('/api/v1/categories/999')
        assert resp.status_code == 404


class TestDeleteCategory:
    def test_no_auth(self, client):
        resp = client.delete('/api/v1/categories/1', json={})
        assert resp.status_code == 401

    @patch('app.routes.v1.category_routes_v1.delete_category')
    def test_success(self, mock_svc, client, admin_headers):
        mock_svc.return_value = ValidationResponse(success=True, message="Category 1 soft-deleted", status_code=200)
        resp = client.delete('/api/v1/categories/1', json={}, headers=admin_headers)
        assert resp.status_code == 200

    @patch('app.routes.v1.category_routes_v1.delete_category')
    def test_not_found(self, mock_svc, client, admin_headers):
        mock_svc.return_value = ValidationResponse(success=False, message="Category not found", status_code=404)
        resp = client.delete('/api/v1/categories/999', json={}, headers=admin_headers)
        assert resp.status_code == 404

    @patch('app.routes.v1.category_routes_v1.delete_category')
    def test_hard_delete_admin_blocked(self, mock_svc, client, admin_headers):
        mock_svc.return_value = ValidationResponse(success=False, message="Only superadmin can perform hard delete", status_code=403)
        resp = client.delete('/api/v1/categories/1', json={'action': 'hard'}, headers=admin_headers)
        assert resp.status_code == 403


# =============================================================================
# INTEGRATION TESTS — Real DB operations (no mocks)
# =============================================================================
from app.models import User, Product, Category
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from decimal import Decimal




# --- Integration tests (real test DB) ---
from app.models import Category, Product, User
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from decimal import Decimal


class TestCategoryIntegrationCRUD:
    def test_admin_creates_category(self, app, db_session, client):
        admin = User(username='catadm', email='catadm@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add(admin)
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/categories/', headers=headers, json={'name': 'electronics'})
        assert resp.status_code == 201
        assert resp.get_json()['success'] is True

    def test_get_category_by_id(self, app, db_session, client):
        cat = Category(name='getcat')
        db_session.add(cat)
        db_session.commit()
        resp = client.get(f'/api/v1/categories/{cat.id}')
        assert resp.status_code == 200

    def test_get_all_categories(self, app, db_session, client):
        db_session.add(Category(name='cat_a'))
        db_session.add(Category(name='cat_b'))
        db_session.commit()
        resp = client.get('/api/v1/categories/')
        assert resp.status_code == 200
        assert resp.get_json()['pagination']['total'] >= 2

    def test_update_category(self, app, db_session, client):
        admin = User(username='catupd', email='catupd@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add(admin)
        cat = Category(name='oldname')
        db_session.add(cat)
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.put(f'/api/v1/categories/{cat.id}', headers=headers, json={'name': 'newname'})
        assert resp.status_code == 200

    def test_soft_delete_category(self, app, db_session, client):
        admin = User(username='catdel', email='catdel@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add(admin)
        cat = Category(name='todelete')
        db_session.add(cat)
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/categories/{cat.id}', headers=headers, json={})
        assert resp.status_code == 200

    def test_hard_delete_superadmin(self, app, db_session, client):
        sa = User(username='catsa', email='catsa@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SUPERADMIN])
        db_session.add(sa)
        cat = Category(name='harddelcat')
        db_session.add(cat)
        db_session.commit()
        token = create_access_token(identity=str(sa.id), additional_claims={'roles': ['SUPERADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/categories/{cat.id}', headers=headers, json={'action': 'hard'})
        assert resp.status_code == 200

    def test_get_category_products(self, app, db_session, client):
        seller = User(username='catseller', email='catseller@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        cat = Category(name='catprods')
        db_session.add(cat)
        db_session.commit()
        prod = Product(user_id=seller.id, name='catprod1', slug='catprod1', uuid='cpuuid1',
            stock=10, brand='b', description='d', price=Decimal('100'), is_active=True)
        prod.categories = [cat]
        db_session.add(prod)
        db_session.commit()
        resp = client.get(f'/api/v1/categories/{cat.id}/products')
        assert resp.status_code == 200
        assert len(resp.get_json()['data']) >= 1
