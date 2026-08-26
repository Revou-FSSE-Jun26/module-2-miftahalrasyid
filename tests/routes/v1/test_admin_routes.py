"""Route tests for admin — mock service layer."""
from unittest.mock import patch, MagicMock


class TestAdminProducts:
    def test_no_auth(self, client):
        resp = client.get('/api/v1/admin/products')
        assert resp.status_code == 401

    def test_buyer_forbidden(self, client, buyer_headers):
        resp = client.get('/api/v1/admin/products', headers=buyer_headers)
        assert resp.status_code == 403

    @patch('app.routes.v1.admin_routes_v1.paginate_query')
    @patch('app.routes.v1.admin_routes_v1.Product')
    def test_admin_success(self, mock_product, mock_paginate, client, admin_headers):
        mock_p = MagicMock()
        mock_p.to_dict.return_value = {'id': 1, 'name': 'Laptop'}
        mock_paginate.return_value = {'items': [mock_p], 'page': 1, 'per_page': 10, 'total': 1, 'pages': 1, 'count': 1}
        resp = client.get('/api/v1/admin/products', headers=admin_headers)
        assert resp.status_code == 200


class TestAdminUserOrders:
    def test_no_auth(self, client):
        resp = client.get('/api/v1/admin/users/1/orders')
        assert resp.status_code == 401

    def test_buyer_forbidden(self, client, buyer_headers):
        resp = client.get('/api/v1/admin/users/1/orders', headers=buyer_headers)
        assert resp.status_code == 403

    @patch('app.routes.v1.admin_routes_v1.get_order_items')
    @patch('app.routes.v1.admin_routes_v1.paginate_query')
    @patch('app.routes.v1.admin_routes_v1.User')
    @patch('app.routes.v1.admin_routes_v1.Order')
    def test_admin_success(self, mock_order, mock_user, mock_paginate, mock_items, client, admin_headers):
        mock_user.query.get.return_value = MagicMock()
        mock_o = MagicMock()
        mock_o.id = 1
        mock_o.to_dict.return_value = {'id': 1, 'name': 'order1'}
        mock_paginate.return_value = {'items': [mock_o], 'page': 1, 'per_page': 10, 'total': 1, 'pages': 1, 'count': 1}
        mock_items.return_value = []
        resp = client.get('/api/v1/admin/users/1/orders', headers=admin_headers)
        assert resp.status_code == 200


class TestAdminUserProfile:
    def test_no_auth(self, client):
        resp = client.get('/api/v1/admin/users/1/profile')
        assert resp.status_code == 401

    def test_buyer_forbidden(self, client, buyer_headers):
        resp = client.get('/api/v1/admin/users/1/profile', headers=buyer_headers)
        assert resp.status_code == 403


# --- Integration tests using test DB ---
from app.models import User, Product, Order, Category, Profile, Address
from app.models.user_model import UserRole, AuthProvider
from app.models.order_model import OrderStatus
from app.models.order_items_model import Order_item
from app.extensions import db
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from decimal import Decimal


class TestAdminProductsIntegration:
    def test_shows_all_including_deleted(self, app, db_session, client):
        seller = User(username='admseller', email='admseller@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        p1 = Product(user_id=seller.id, name='active prod', slug='active-prod-adm', uuid='uadm1',
            stock=10, brand='b', description='d', price=Decimal('100'), is_active=True)
        p2 = Product(user_id=seller.id, name='deleted prod', slug='deleted-prod-adm', uuid='uadm2',
            stock=5, brand='b', description='d', price=Decimal('50'), is_active=False)
        db_session.add_all([p1, p2])
        db_session.commit()
        admin = User(username='admuser', email='admuser@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add(admin)
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get('/api/v1/admin/products', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert len(data) >= 2


class TestAdminUserOrdersIntegration:
    def test_returns_user_orders(self, app, db_session, client):
        buyer = User(username='admbuyer', email='admbuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        order = Order(user_id=buyer.id, name='adm order', status=OrderStatus.PAID,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        db_session.add(order)
        db_session.commit()
        admin = User(username='admuser2', email='admuser2@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add(admin)
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get(f'/api/v1/admin/users/{buyer.id}/orders', headers=headers)
        assert resp.status_code == 200
        assert len(resp.get_json()['data']) >= 1


class TestAdminUserProfileIntegration:
    def test_returns_profile(self, app, db_session, client):
        user = User(username='profuser', email='profuser@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        profile = Profile(user_id=user.id, bio='Test bio')
        db_session.add(profile)
        db_session.commit()
        admin = User(username='admuser3', email='admuser3@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add(admin)
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get(f'/api/v1/admin/users/{user.id}/profile', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['bio'] == 'Test bio'


class TestAdminUserAddressesIntegration:
    def test_returns_addresses(self, app, db_session, client):
        user = User(username='admaddr', email='admaddr@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(user_id=user.id, label='Home', recipient_name='T', phone='+6281234567890',
            address_line='St', city='C', province='P', postal_code='1', is_default=True)
        db_session.add(addr)
        db_session.commit()
        admin = User(username='admuser4', email='admuser4@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add(admin)
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get(f'/api/v1/admin/users/{user.id}/addresses', headers=headers)
        assert resp.status_code == 200
        assert len(resp.get_json()['data']) == 1
