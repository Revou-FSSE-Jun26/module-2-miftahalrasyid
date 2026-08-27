"""Route tests for orders — mock service layer."""
from unittest.mock import patch, MagicMock
from app.services import ValidationResponse


class TestGetOrders:
    def test_no_auth(self, client):
        resp = client.get('/api/v1/orders/')
        assert resp.status_code == 401

    @patch('app.routes.v1.orders_routes_v1.get_order_items')
    @patch('app.routes.v1.orders_routes_v1.get_all_orders')
    def test_buyer_success(self, mock_svc, mock_items, client, buyer_headers):
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.to_dict.return_value = {'id': 1, 'name': 'order1', 'status': 'PAID', 'total': 100.0}
        mock_svc.return_value = {'items': [mock_order], 'page': 1, 'per_page': 10, 'total': 1, 'pages': 1, 'count': 1}
        mock_items.return_value = []
        resp = client.get('/api/v1/orders/', headers=buyer_headers)
        assert resp.status_code == 200


class TestPostOrder:
    def test_no_auth(self, client):
        resp = client.post('/api/v1/orders/', json={'name': 'test', 'items': []})
        assert resp.status_code == 401

    def test_seller_forbidden(self, client, seller_headers):
        resp = client.post('/api/v1/orders/', json={'name': 'test', 'items': [{'product_id': 1, 'quantity': 1}]}, headers=seller_headers)
        assert resp.status_code == 403


class TestDeleteOrder:
    def test_no_auth(self, client):
        resp = client.delete('/api/v1/orders/1', json={})
        assert resp.status_code == 401

    @patch('app.routes.v1.orders_routes_v1.delete_order')
    def test_success(self, mock_svc, client, buyer_headers):
        mock_svc.return_value = ValidationResponse(success=True, message="Order 1 soft-deleted", status_code=200)
        resp = client.delete('/api/v1/orders/1', json={}, headers=buyer_headers)
        assert resp.status_code == 200

    @patch('app.routes.v1.orders_routes_v1.delete_order')
    def test_not_found(self, mock_svc, client, buyer_headers):
        mock_svc.return_value = ValidationResponse(success=False, message="Order not found", status_code=404)
        resp = client.delete('/api/v1/orders/999', json={}, headers=buyer_headers)
        assert resp.status_code == 404

    @patch('app.routes.v1.orders_routes_v1.delete_order')
    def test_cannot_cancel_completed(self, mock_svc, client, buyer_headers):
        mock_svc.return_value = ValidationResponse(success=False, message="Can only cancel orders with PAID status", status_code=400)
        resp = client.delete('/api/v1/orders/1', json={}, headers=buyer_headers)
        assert resp.status_code == 400


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




class TestOrderIntegrationCRUD:
    def test_buyer_creates_order(self, app, db_session, client):
        seller = User(username='ordseller', email='ordseller@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='OrdProd', slug='ordprod', uuid='orduuid1',
            stock=20, brand='B', description='D', price=Decimal('500'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='ordbuyer', email='ordbuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/orders/', headers=headers, json={
            'name': 'test order', 'items': [{'product_id': prod.id, 'quantity': 2}]
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['status'] == 'PENDING'

    def test_create_order_insufficient_stock(self, app, db_session, client):
        seller = User(username='ordstock', email='ordstock@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='LowStock', slug='lowstock', uuid='lowuuid',
            stock=1, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='ordbuyer2', email='ordbuyer2@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/orders/', headers=headers, json={
            'name': 'big order', 'items': [{'product_id': prod.id, 'quantity': 99}]
        })
        assert resp.status_code == 400
        assert 'Insufficient stock' in resp.get_json()['message']

    def test_create_order_empty_items(self, app, db_session, client):
        buyer = User(username='ordnoitems', email='ordnoitems@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/orders/', headers=headers, json={
            'name': 'empty order', 'items': []
        })
        assert resp.status_code == 400

    def test_create_order_product_not_found(self, app, db_session, client):
        buyer = User(username='ordnoprod', email='ordnoprod@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/orders/', headers=headers, json={
            'name': 'ghost order', 'items': [{'product_id': 99999, 'quantity': 1}]
        })
        assert resp.status_code == 400
        assert 'not found' in resp.get_json()['message']

    def test_get_order_by_id(self, app, db_session, client):
        buyer = User(username='orddetail', email='orddetail@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        order = Order(user_id=buyer.id, name='detail order', status=OrderStatus.PAID,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        db_session.add(order)
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get(f'/api/v1/orders/{order.id}', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['name'] == 'detail order'

    def test_get_order_not_found(self, app, db_session, client):
        buyer = User(username='ordnf', email='ordnf@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get('/api/v1/orders/99999', headers=headers)
        assert resp.status_code == 404

    def test_get_all_orders_buyer(self, app, db_session, client):
        buyer = User(username='ordall', email='ordall@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        o1 = Order(user_id=buyer.id, name='order a', status=OrderStatus.PAID,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        o2 = Order(user_id=buyer.id, name='order b', status=OrderStatus.PAID,
            subtotal=Decimal('200'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('22'), total=Decimal('222'))
        db_session.add_all([o1, o2])
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get('/api/v1/orders/', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['pagination']['total'] >= 2

    def test_seller_updates_order_status(self, app, db_session, client):
        seller = User(username='ordselupd', email='ordselupd@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='UpdProd', slug='updprod-ord', uuid='upduuid2',
            stock=20, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='ordselbuyer', email='ordselbuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        order = Order(user_id=buyer.id, name='to complete', status=OrderStatus.PAID,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        db_session.add(order)
        db_session.commit()
        oi = Order_item(order_id=order.id, product_id=prod.id, quantity=1, compound_price=Decimal('100'))
        db_session.add(oi)
        db_session.commit()
        token = create_access_token(identity=str(seller.id), additional_claims={'roles': ['SELLER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.put(f'/api/v1/orders/{order.id}', headers=headers, json={'status': 'COMPLETED'})
        assert resp.status_code == 200
        assert resp.get_json()['data']['status'] == 'COMPLETED'

    def test_buyer_cancels_order(self, app, db_session, client):
        seller = User(username='ordcancsell', email='ordcancsell@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='CancelProd', slug='cancelprod', uuid='canceluuid',
            stock=20, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='ordcancbuyer', email='ordcancbuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        order = Order(user_id=buyer.id, name='cancel order', status=OrderStatus.CANCELED,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        db_session.add(order)
        db_session.commit()
        oi = Order_item(order_id=order.id, product_id=prod.id, quantity=2, compound_price=Decimal('200'))
        db_session.add(oi)
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/orders/{order.id}', headers=headers, json={})
        assert resp.status_code == 200
        # Stock unchanged (already restored during CANCELED transition)
        db_session.refresh(prod)
        assert prod.stock == 20

    def test_superadmin_hard_deletes_order(self, app, db_session, client):
        seller = User(username='ordhardsell', email='ordhardsell@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='HardDelProd', slug='harddelprod-ord', uuid='hdorduuid',
            stock=20, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='ordhardbuyer', email='ordhardbuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        order = Order(user_id=buyer.id, name='hard del order', status=OrderStatus.PAID,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        db_session.add(order)
        db_session.commit()
        oi = Order_item(order_id=order.id, product_id=prod.id, quantity=1, compound_price=Decimal('100'))
        db_session.add(oi)
        db_session.commit()
        sa = User(username='ordsa', email='ordsa@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SUPERADMIN])
        db_session.add(sa)
        db_session.commit()
        token = create_access_token(identity=str(sa.id), additional_claims={'roles': ['SUPERADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/orders/{order.id}', headers=headers, json={'action': 'hard'})
        assert resp.status_code == 200

    def test_get_order_products(self, app, db_session, client):
        seller = User(username='ordprodget', email='ordprodget@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='OrdProdGet', slug='ordprodget', uuid='opgtuuid',
            stock=20, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='ordprodbuyer', email='ordprodbuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        order = Order(user_id=buyer.id, name='prod order', status=OrderStatus.PAID,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        db_session.add(order)
        db_session.commit()
        oi = Order_item(order_id=order.id, product_id=prod.id, quantity=3, compound_price=Decimal('300'))
        db_session.add(oi)
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get(f'/api/v1/orders/{order.id}/products', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert len(data) >= 1
        assert data[0]['quantity'] == 3

    def test_create_order_duplicate_product(self, app, db_session, client):
        seller = User(username='orddup', email='orddup@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='DupProd', slug='dupprod-ord', uuid='dupuuid2',
            stock=20, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='orddupbuyer', email='orddupbuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/orders/', headers=headers, json={
            'name': 'dup order', 'items': [
                {'product_id': prod.id, 'quantity': 1},
                {'product_id': prod.id, 'quantity': 2}
            ]
        })
        assert resp.status_code == 400
        assert 'Duplicate' in resp.get_json()['message']
