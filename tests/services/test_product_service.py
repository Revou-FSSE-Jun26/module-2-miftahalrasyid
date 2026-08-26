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
