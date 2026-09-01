from app.models import User, Product
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from decimal import Decimal
from app.services import ValidationResponse


class TestGetAllProducts:
    def test_returns_paginated(self, app, db_session):
        
            from app.services.product_service import get_all_products
            # Empty DB should still return pagination structure
            with app.test_request_context('/?page=1&per_page=10'):
                result = get_all_products()
                assert result is not None
                assert 'items' in result
                assert 'page' in result


class TestDeleteProduct:
    def test_not_found(self, app, db_session):
        
            from app.services.product_service import delete_product
            result = delete_product(99999, '1', ['ADMIN'], 'soft')
            assert result.success is False
            assert result.status_code == 404

    def test_no_permission(self, app, db_session):
        
            seller = User(username='s_del', email='s_del@test.com', age=30, is_active=True,
                provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
                roles=[UserRole.SELLER])
            db_session.add(seller)
            db_session.commit()
            product = Product(user_id=seller.id, name='del_prod', slug='del-prod', uuid='uuid-del',
                stock=5, brand='b', description='d', price=Decimal('10'), is_active=True)
            db_session.add(product)
            db_session.commit()
            from app.services.product_service import delete_product
            result = delete_product(product.id, str(seller.id), ['BUYER'], 'soft')
            assert result.success is False
            assert result.status_code == 403

    def test_soft_delete_success(self, app, db_session):
        seller = User(username='s_soft', email='s_soft@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        product = Product(user_id=seller.id, name='soft_prod', slug='soft-prod', uuid='uuid-soft',
            stock=5, brand='b', description='d', price=Decimal('10'), is_active=True)
        db_session.add(product)
        db_session.commit()
        from app.services.product_service import delete_product
        result = delete_product(product.id, str(seller.id), ['SELLER'], 'soft')
        assert result.success is True
        assert result.status_code == 200

    def test_blocked_by_paid_order(self, app, db_session):
        """Product linked to a PAID order cannot be deleted (409)."""
        from app.models.order_model import Order, OrderStatus
        from app.models.order_items_model import Order_item
        seller = User(username='s_paid', email='s_paid@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        buyer = User(username='b_paid', email='b_paid@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add_all([seller, buyer])
        db_session.commit()
        product = Product(user_id=seller.id, name='paid_prod', slug='paid-prod', uuid='uuid-paid',
            stock=5, brand='b', description='d', price=Decimal('100'), is_active=True)
        db_session.add(product)
        db_session.commit()
        order = Order(user_id=buyer.id, name='paid order', status=OrderStatus.PAID,
            subtotal=Decimal('100'), discount_percent=0, discount_amount=0,
            tax_percent=11, tax_amount=Decimal('11'), total=Decimal('111'))
        db_session.add(order)
        db_session.commit()
        db_session.add(Order_item(order_id=order.id, product_id=product.id, quantity=1,
            compound_price=Decimal('100')))
        db_session.commit()
        from app.services.product_service import delete_product
        result = delete_product(product.id, str(seller.id), ['SELLER'], 'soft')
        assert result.success is False
        assert result.status_code == 409


class TestCreateNewProduct:
    def test_seller_creates_own_product(self, app, db_session):
        seller = User(username='s_create', email='s_create@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        product = Product(name='new_prod', brand='b', description='d',
            price=Decimal('50'), stock=3, is_active=True)
        from app.services.product_service import create_new_product
        with app.test_request_context('/', json={}):
            result = create_new_product(str(seller.id), product, ['SELLER'])
        assert result is not None
        assert not isinstance(result, ValidationResponse)
        assert result.user_id == seller.id
        assert result.slug  # auto-generated

    def test_invalid_category_ids(self, app, db_session):
        seller = User(username='s_badcat', email='s_badcat@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        product = Product(name='badcat_prod', brand='b', description='d',
            price=Decimal('50'), stock=3, is_active=True)
        from app.services.product_service import create_new_product
        with app.test_request_context('/', json={'category_ids': [99999]}):
            result = create_new_product(str(seller.id), product, ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'category' in result.message.lower()


class TestUpdateProduct:
    def test_owner_updates(self, app, db_session):
        seller = User(username='s_upd', email='s_upd@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        product = Product(user_id=seller.id, name='old_prod', slug='old-prod', uuid='uuid-upd',
            stock=5, brand='b', description='d', price=Decimal('10'), is_active=True)
        db_session.add(product)
        db_session.commit()
        from app.services.product_service import update_product
        result = update_product(product.id, {'name': 'new_prod_name', 'price': Decimal('20')},
            str(seller.id), ['SELLER'])
        assert not isinstance(result, ValidationResponse)
        assert result.name == 'new_prod_name'

    def test_not_owner_unauthorized(self, app, db_session):
        owner = User(username='owner_p', email='owner_p@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        other = User(username='other_p', email='other_p@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add_all([owner, other])
        db_session.commit()
        product = Product(user_id=owner.id, name='owned', slug='owned-prod', uuid='uuid-owned',
            stock=5, brand='b', description='d', price=Decimal('10'), is_active=True)
        db_session.add(product)
        db_session.commit()
        from app.services.product_service import update_product
        result = update_product(product.id, {'name': 'hijack'}, str(other.id), ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'Unauthorized' in result.message

    def test_not_found(self, app, db_session):
        from app.services.product_service import update_product
        result = update_product(99999, {'name': 'ghost'}, '1', ['ADMIN'])
        assert isinstance(result, ValidationResponse)
        assert 'not found' in result.message.lower()
