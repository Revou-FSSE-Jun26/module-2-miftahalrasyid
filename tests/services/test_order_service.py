"""Service tests for orders — mock DB layer."""
from unittest.mock import patch, MagicMock


class TestDeleteOrder:
    @patch('app.permissions.field_filter.get_delete_policy')
    @patch('app.services.order_service.Order')
    def test_not_found(self, mock_order, mock_policy, app):
        
            mock_order.query.filter.return_value.first.return_value = None
            from app.services.order_service import delete_order
            result = delete_order(999, '1', ['BUYER'], 'soft')
            assert result.success is False
            assert result.status_code == 404

    @patch('app.permissions.field_filter.get_delete_policy')
    @patch('app.services.order_service.Order')
    def test_no_permission(self, mock_order, mock_policy, app):
        
            mock_order.query.filter.return_value.first.return_value = MagicMock()
            mock_policy.return_value = None
            from app.services.order_service import delete_order
            result = delete_order(1, '1', ['BUYER'], 'soft')
            assert result.success is False
            assert result.status_code == 403


class TestValidateStatusTransition:
    def test_paid_to_completed(self, app):
        
            from app.services.order_service import _validate_status_transition
            from app.models.order_model import OrderStatus
            assert _validate_status_transition(OrderStatus.PAID, OrderStatus.COMPLETED) is True

    def test_paid_to_canceled(self, app):
        
            from app.services.order_service import _validate_status_transition
            from app.models.order_model import OrderStatus
            assert _validate_status_transition(OrderStatus.PAID, OrderStatus.CANCELED) is True

    def test_completed_to_paid_invalid(self, app):
        
            from app.services.order_service import _validate_status_transition
            from app.models.order_model import OrderStatus
            assert _validate_status_transition(OrderStatus.COMPLETED, OrderStatus.PAID) is False

    def test_canceled_to_anything_invalid(self, app):
        
            from app.services.order_service import _validate_status_transition
            from app.models.order_model import OrderStatus
            assert _validate_status_transition(OrderStatus.CANCELED, OrderStatus.COMPLETED) is False

from app.models import User, Product, Order, Category
from app.models.user_model import UserRole, AuthProvider
from app.models.order_model import OrderStatus
from app.models.order_items_model import Order_item
from app.extensions import db
from werkzeug.security import generate_password_hash
from decimal import Decimal


class TestCreateOrder:
    def test_create_order_success(self, app, db_session):
        
            # Create seller + product
            seller = User(username='seller1', email='seller_test1@test.com', age=30, is_active=True,
                provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
                roles=[UserRole.SELLER])
            db_session.add(seller)
            db_session.commit()
            product = Product(user_id=seller.id, name='test prod', slug='test-prod-1', uuid='uuid1',
                stock=10, brand='brand', description='desc', price=Decimal('100'), is_active=True)
            db_session.add(product)
            db_session.commit()
            # Create buyer (separate from seller to avoid self-purchase block)
            buyer = User(username='buyer1', email='buyer_test1@test.com', age=25, is_active=True,
                provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
                roles=[UserRole.BUYER])
            db_session.add(buyer)
            db_session.commit()
            # Create order instance
            order = Order(name='test order')
            from app.services.order_service import create_order
            result = create_order(order, [{'product_id': product.id, 'quantity': 2}], str(buyer.id), ['BUYER'])
            assert result is not None
            assert result.status == OrderStatus.PENDING
            # Stock NOT deducted (deducted on payment)
            assert product.stock == 10

    def test_create_order_insufficient_stock(self, app, db_session):
        
            seller = User(username='seller2', email='seller_test2@test.com', age=30, is_active=True,
                provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
                roles=[UserRole.SELLER])
            db_session.add(seller)
            db_session.commit()
            product = Product(user_id=seller.id, name='low stock', slug='low-stock-1', uuid='uuid2',
                stock=1, brand='brand', description='desc', price=Decimal('50'), is_active=True)
            db_session.add(product)
            db_session.commit()
            buyer = User(username='buyer2', email='buyer_test2@test.com', age=25, is_active=True,
                provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
                roles=[UserRole.BUYER])
            db_session.add(buyer)
            db_session.commit()
            order = Order(name='fail order')
            from app.services.order_service import create_order
            from app.services import ValidationResponse
            result = create_order(order, [{'product_id': product.id, 'quantity': 5}], str(buyer.id), ['BUYER'])
            assert isinstance(result, ValidationResponse)
            assert 'Insufficient stock' in result.message
