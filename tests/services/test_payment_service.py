import pytest
from decimal import Decimal
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token

from app.models.user_model import User, UserRole, AuthProvider
from app.models.product_model import Product
from app.models.order_model import Order, OrderStatus
from app.models.order_items_model import Order_item
from app.models.address_model import Address
from app.services.payment_service import process_payment
from app.services import ValidationResponse


class TestProcessPayment:
    """Unit tests for payment_service.process_payment"""

    _counter = 0

    @classmethod
    def _next_id(cls):
        cls._counter += 1
        return cls._counter

    def _create_seller(self, db_session):
        n = self._next_id()
        seller = User(username=f'payseller{n}', email=f'payseller{n}@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        return seller

    def _create_buyer(self, db_session):
        n = self._next_id()
        buyer = User(username=f'paybuyer{n}', email=f'paybuyer{n}@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        return buyer

    def _create_product(self, db_session, seller, stock=10):
        n = self._next_id()
        prod = Product(user_id=seller.id, name=f'PayProd{n}', slug=f'payprod{n}', uuid=f'payuuid{n}',
            stock=stock, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        return prod

    def _create_pending_order(self, db_session, buyer, product, quantity=2):
        order = Order(user_id=buyer.id, name='pay order', status=OrderStatus.PENDING,
            subtotal=Decimal('200'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('22'), total=Decimal('222'))
        db_session.add(order)
        db_session.commit()
        oi = Order_item(order_id=order.id, product_id=product.id, quantity=quantity,
            compound_price=Decimal('200'))
        db_session.add(oi)
        db_session.commit()
        return order

    def _create_address(self, db_session, buyer, is_default=True):
        addr = Address(user_id=buyer.id, label='Home', recipient_name='Buyer',
            phone='+6281234567890', address_line='Jl. Test 1', city='Jakarta',
            province='DKI Jakarta', postal_code='12345', is_default=is_default)
        db_session.add(addr)
        db_session.commit()
        return addr

    def test_payment_success_with_default_address(self, app, db_session):
        """Payment succeeds using default address, stock deducted, status PAID."""
        with app.app_context():
            seller = self._create_seller(db_session)
            buyer = self._create_buyer(db_session)
            product = self._create_product(db_session, seller, stock=10)
            order = self._create_pending_order(db_session, buyer, product, quantity=3)
            address = self._create_address(db_session, buyer, is_default=True)

            result = process_payment(order.id, str(buyer.id))

            assert not isinstance(result, ValidationResponse)
            assert result.status == OrderStatus.PAID
            assert result.address_id == address.id
            db_session.refresh(product)
            assert product.stock == 7  # 10 - 3

    def test_payment_success_with_explicit_address(self, app, db_session):
        """Payment succeeds with explicit address_id override."""
        with app.app_context():
            seller = self._create_seller(db_session)
            buyer = self._create_buyer(db_session)
            product = self._create_product(db_session, seller, stock=10)
            order = self._create_pending_order(db_session, buyer, product, quantity=2)
            default_addr = self._create_address(db_session, buyer, is_default=True)
            # Create a second non-default address
            other_addr = Address(user_id=buyer.id, label='Office', recipient_name='Buyer Office',
                phone='+6289876543210', address_line='Jl. Office 2', city='Bandung',
                province='Jawa Barat', postal_code='40123', is_default=False)
            db_session.add(other_addr)
            db_session.commit()

            result = process_payment(order.id, str(buyer.id), address_id=other_addr.id)

            assert not isinstance(result, ValidationResponse)
            assert result.status == OrderStatus.PAID
            assert result.address_id == other_addr.id

    def test_payment_fails_no_default_address(self, app, db_session):
        """Payment fails when no address_id provided and no default address exists."""
        with app.app_context():
            seller = self._create_seller(db_session)
            buyer = self._create_buyer(db_session)
            product = self._create_product(db_session, seller, stock=10)
            order = self._create_pending_order(db_session, buyer, product)

            result = process_payment(order.id, str(buyer.id))

            assert isinstance(result, ValidationResponse)
            assert result.success is False
            assert "Default address is not set" in result.message

    def test_payment_fails_order_not_pending(self, app, db_session):
        """Payment fails when order is not in PENDING status."""
        with app.app_context():
            seller = self._create_seller(db_session)
            buyer = self._create_buyer(db_session)
            product = self._create_product(db_session, seller, stock=10)
            address = self._create_address(db_session, buyer)
            # Create order with PAID status
            order = Order(user_id=buyer.id, name='paid order', status=OrderStatus.PAID,
                subtotal=Decimal('200'), discount_percent=0, discount_amount=0,
                tax_percent=11, tax_amount=Decimal('22'), total=Decimal('222'))
            db_session.add(order)
            db_session.commit()

            result = process_payment(order.id, str(buyer.id))

            assert isinstance(result, ValidationResponse)
            assert "Only PENDING orders can be paid" in result.message

    def test_payment_fails_not_owner(self, app, db_session):
        """Payment fails when user doesn't own the order."""
        with app.app_context():
            seller = self._create_seller(db_session)
            buyer = self._create_buyer(db_session)
            product = self._create_product(db_session, seller, stock=10)
            order = self._create_pending_order(db_session, buyer, product)
            # Another user tries to pay
            other = User(username='other', email='other@test.com', age=20, is_active=True,
                provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
                roles=[UserRole.BUYER])
            db_session.add(other)
            db_session.commit()
            self._create_address(db_session, other)

            result = process_payment(order.id, str(other.id))

            assert isinstance(result, ValidationResponse)
            assert "Unauthorized" in result.message

    def test_payment_fails_insufficient_stock(self, app, db_session):
        """Payment fails when product stock is insufficient at payment time."""
        with app.app_context():
            seller = self._create_seller(db_session)
            buyer = self._create_buyer(db_session)
            product = self._create_product(db_session, seller, stock=1)
            order = self._create_pending_order(db_session, buyer, product, quantity=5)
            self._create_address(db_session, buyer)

            result = process_payment(order.id, str(buyer.id))

            assert isinstance(result, ValidationResponse)
            assert "Insufficient stock" in result.message
            # Stock unchanged
            db_session.refresh(product)
            assert product.stock == 1

    def test_payment_fails_order_not_found(self, app, db_session):
        """Payment fails for non-existent order."""
        with app.app_context():
            buyer = self._create_buyer(db_session)
            self._create_address(db_session, buyer)

            result = process_payment(9999, str(buyer.id))

            assert isinstance(result, ValidationResponse)
            assert "Order not found" in result.message

    def test_payment_fails_address_not_found(self, app, db_session):
        """Payment fails when explicit address_id doesn't belong to user."""
        with app.app_context():
            seller = self._create_seller(db_session)
            buyer = self._create_buyer(db_session)
            product = self._create_product(db_session, seller, stock=10)
            order = self._create_pending_order(db_session, buyer, product)

            result = process_payment(order.id, str(buyer.id), address_id=9999)

            assert isinstance(result, ValidationResponse)
            assert "Address not found" in result.message

    def test_payment_fails_product_inactive(self, app, db_session):
        """Payment fails when product becomes inactive between order creation and payment."""
        with app.app_context():
            seller = self._create_seller(db_session)
            buyer = self._create_buyer(db_session)
            product = self._create_product(db_session, seller, stock=10)
            order = self._create_pending_order(db_session, buyer, product)
            self._create_address(db_session, buyer)
            # Deactivate product after order was created
            product.is_active = False
            db_session.commit()

            result = process_payment(order.id, str(buyer.id))

            assert isinstance(result, ValidationResponse)
            assert "no longer available" in result.message


class TestPaymentRoute:
    """Integration tests for POST /api/v1/payment/"""

    def test_payment_route_success(self, app, db_session, client):
        """Full integration: buyer pays pending order via route."""
        seller = User(username='routeseller', email='routeseller@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='RouteProd', slug='routeprod', uuid='routeuuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='routebuyer', email='routebuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        addr = Address(user_id=buyer.id, label='Home', recipient_name='Route Buyer',
            phone='+6281234567890', address_line='Jl. Route', city='Jakarta',
            province='DKI Jakarta', postal_code='10110', is_default=True)
        db_session.add(addr)
        db_session.commit()
        order = Order(user_id=buyer.id, name='route order', status=OrderStatus.PENDING,
            subtotal=Decimal('200'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('22'), total=Decimal('222'))
        db_session.add(order)
        db_session.commit()
        oi = Order_item(order_id=order.id, product_id=prod.id, quantity=2,
            compound_price=Decimal('200'))
        db_session.add(oi)
        db_session.commit()

        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        resp = client.post('/api/v1/payment/', headers=headers, json={'order_id': order.id})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['status'] == 'PAID'
        assert data['data']['address_id'] == addr.id
        # Stock deducted
        db_session.refresh(prod)
        assert prod.stock == 8

    def test_payment_route_no_address(self, app, db_session, client):
        """Route returns 400 when buyer has no default address."""
        seller = User(username='noaddrseller', email='noaddrseller@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='NoAddrProd', slug='noaddrprod', uuid='noaddruuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        buyer = User(username='noaddrbuyer', email='noaddrbuyer@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(buyer)
        db_session.commit()
        order = Order(user_id=buyer.id, name='noaddr order', status=OrderStatus.PENDING,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        db_session.add(order)
        db_session.commit()
        oi = Order_item(order_id=order.id, product_id=prod.id, quantity=1,
            compound_price=Decimal('100'))
        db_session.add(oi)
        db_session.commit()

        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        resp = client.post('/api/v1/payment/', headers=headers, json={'order_id': order.id})
        assert resp.status_code == 400
        data = resp.get_json()
        assert "Default address is not set" in data['message']

    def test_payment_route_seller_forbidden(self, app, db_session, client):
        """Route returns 403 when seller-only role tries to pay."""
        seller = User(username='sellonly', email='sellonly@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()

        token = create_access_token(identity=str(seller.id), additional_claims={'roles': ['SELLER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        resp = client.post('/api/v1/payment/', headers=headers, json={'order_id': 1})
        assert resp.status_code == 403
