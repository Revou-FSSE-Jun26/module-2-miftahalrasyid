"""Route tests for products — mock service layer."""
from unittest.mock import patch, MagicMock
from app.services import ValidationResponse


class TestGetProducts:
    @patch('app.routes.v1.product_routes_v1.get_all_products')
    def test_get_products_success(self, mock_svc, client):
        mock_product = MagicMock()
        mock_product.to_dict.return_value = {'id': 1, 'name': 'Laptop', 'price': 5000000.0}
        mock_svc.return_value = {'items': [mock_product], 'page': 1, 'per_page': 10, 'total': 1, 'pages': 1, 'count': 1}
        resp = client.get('/api/v1/products/')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert len(data['data']) == 1

    @patch('app.routes.v1.product_routes_v1.get_all_products')
    def test_get_products_empty(self, mock_svc, client):
        mock_svc.return_value = {'items': [], 'page': 1, 'per_page': 10, 'total': 0, 'pages': 0, 'count': 0}
        resp = client.get('/api/v1/products/')
        assert resp.status_code == 200
        assert resp.get_json()['data'] == []

    @patch('app.routes.v1.product_routes_v1.get_all_products')
    def test_get_products_failure(self, mock_svc, client):
        mock_svc.return_value = None
        resp = client.get('/api/v1/products/')
        assert resp.status_code == 400


class TestGetProductById:
    @patch('app.routes.v1.product_routes_v1.get_product_by_id')
    def test_found(self, mock_svc, client):
        mock_product = MagicMock()
        mock_product.to_dict.return_value = {'id': 1, 'name': 'Laptop'}
        mock_svc.return_value = mock_product
        resp = client.get('/api/v1/products/1')
        assert resp.status_code == 200

    @patch('app.routes.v1.product_routes_v1.get_product_by_id')
    def test_not_found(self, mock_svc, client):
        mock_svc.return_value = None
        resp = client.get('/api/v1/products/999')
        assert resp.status_code == 404


class TestPostProduct:
    def test_no_auth_returns_401_or_422(self, client):
        resp = client.post('/api/v1/products/', json={'name': 'Test'})
        assert resp.status_code in (401, 422)

    def test_buyer_returns_403_or_422(self, client, buyer_headers):
        resp = client.post('/api/v1/products/', json={'name': 'Test'}, headers=buyer_headers)
        assert resp.status_code in (403, 422)


class TestDeleteProduct:
    def test_no_auth_returns_401(self, client):
        resp = client.delete('/api/v1/products/1', json={})
        assert resp.status_code == 401

    @patch('app.routes.v1.product_routes_v1.delete_product')
    def test_success(self, mock_svc, client, seller_headers):
        mock_svc.return_value = ValidationResponse(success=True, message="Product 1 soft-deleted", status_code=200)
        resp = client.delete('/api/v1/products/1', json={}, headers=seller_headers)
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    @patch('app.routes.v1.product_routes_v1.delete_product')
    def test_not_found(self, mock_svc, client, seller_headers):
        mock_svc.return_value = ValidationResponse(success=False, message="Product not found", status_code=404)
        resp = client.delete('/api/v1/products/999', json={}, headers=seller_headers)
        assert resp.status_code == 404

    @patch('app.routes.v1.product_routes_v1.delete_product')
    def test_forbidden(self, mock_svc, client, seller_headers):
        mock_svc.return_value = ValidationResponse(success=False, message="Unauthorized", status_code=403)
        resp = client.delete('/api/v1/products/1', json={}, headers=seller_headers)
        assert resp.status_code == 403


# =============================================================================
# INTEGRATION TESTS — Real DB operations (no mocks)
# =============================================================================
from app.models import User, Product, Order, Category
from app.models.user_model import UserRole, AuthProvider
from app.models.order_model import OrderStatus
from app.models.order_items_model import Order_item
from app.extensions import db
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from decimal import Decimal




class TestProductIntegrationCRUD:
    def test_seller_creates_product(self, app, db_session, client):
        seller = User(username='prodseller', email='prodseller@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        cat = Category(name='prodcat')
        db_session.add(cat)
        db_session.commit()
        token = create_access_token(identity=str(seller.id), additional_claims={'roles': ['SELLER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/products/', headers=headers, json={
            'name': 'Test Laptop', 'slug': 'test-laptop-int', 'brand': 'TestBrand',
            'description': 'A test product', 'price': 5000000, 'stock': 10,
            'user_id': seller.id, 'category_ids': [cat.id]
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['name'] == 'Test Laptop'

    def test_get_product_by_id(self, app, db_session, client):
        seller = User(username='prodget', email='prodget@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='GetProd', slug='getprod', uuid='getprod-uuid',
            stock=5, brand='B', description='D', price=Decimal('200'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        resp = client.get(f'/api/v1/products/{prod.id}')
        assert resp.status_code == 200
        assert resp.get_json()['data']['name'] == 'GetProd'

    def test_get_product_not_found(self, app, db_session, client):
        resp = client.get('/api/v1/products/99999')
        assert resp.status_code == 404

    def test_get_all_products(self, app, db_session, client):
        seller = User(username='prodall', email='prodall@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        p1 = Product(user_id=seller.id, name='Prod1', slug='prod1-int', uuid='p1uuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True)
        p2 = Product(user_id=seller.id, name='Prod2', slug='prod2-int', uuid='p2uuid',
            stock=5, brand='B', description='D', price=Decimal('200'), is_active=True)
        db_session.add_all([p1, p2])
        db_session.commit()
        resp = client.get('/api/v1/products/')
        assert resp.status_code == 200
        assert resp.get_json()['pagination']['total'] >= 2

    def test_seller_updates_product(self, app, db_session, client):
        seller = User(username='produpd', email='produpd@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='OldName', slug='oldname-upd', uuid='upduuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        token = create_access_token(identity=str(seller.id), additional_claims={'roles': ['SELLER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.put(f'/api/v1/products/{prod.id}', headers=headers, json={
            'name': 'NewName', 'slug': 'newname-upd', 'price': 150
        })
        assert resp.status_code == 200
        assert resp.get_json()['data']['name'] == 'NewName'

    def test_seller_soft_deletes_product(self, app, db_session, client):
        seller = User(username='proddel', email='proddel@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='DelProd', slug='delprod-int', uuid='deluuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        token = create_access_token(identity=str(seller.id), additional_claims={'roles': ['SELLER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/products/{prod.id}', headers=headers, json={})
        assert resp.status_code == 200

    def test_superadmin_hard_deletes_product(self, app, db_session, client):
        seller = User(username='prodsa', email='prodsa@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='HardDel', slug='harddel-int', uuid='harduuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        sa = User(username='prodsa2', email='prodsa2@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SUPERADMIN])
        db_session.add(sa)
        db_session.commit()
        token = create_access_token(identity=str(sa.id), additional_claims={'roles': ['SUPERADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/products/{prod.id}', headers=headers, json={'action': 'hard'})
        assert resp.status_code == 200

    def test_cannot_delete_product_with_active_orders(self, app, db_session, client):
        seller = User(username='prodord', email='prodord@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='LinkedProd', slug='linkedprod', uuid='linkuuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='prodbuyer', email='prodbuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        order = Order(user_id=buyer.id, name='linked order', status=OrderStatus.PAID,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        db_session.add(order)
        db_session.commit()
        oi = Order_item(order_id=order.id, product_id=prod.id, quantity=1, compound_price=Decimal('100'))
        db_session.add(oi)
        db_session.commit()
        token = create_access_token(identity=str(seller.id), additional_claims={'roles': ['SELLER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/products/{prod.id}', headers=headers, json={})
        assert resp.status_code == 409
