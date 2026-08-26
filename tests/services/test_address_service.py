from app.models import User, Address
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from app.services import ValidationResponse


class TestCreateAddress:
    def test_success(self, app, db_session):
        
            user = User(username='addr_user', email='addr_user@test.com', age=25, is_active=True,
                provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
                roles=[UserRole.BUYER])
            db_session.add(user)
            db_session.commit()
            addr = Address(label='Home', recipient_name='Test', phone='+6281234567890',
                address_line='123 St', city='Jakarta', province='DKI', postal_code='12345')
            from app.services.address_service import create_address
            result = create_address(user.id, addr)
            assert result is not None
            assert result.is_default is True  # first address is auto-default


class TestDeleteAddress:
    def test_not_found(self, app, db_session):
        
            from app.services.address_service import delete_address
            result = delete_address(99999, 1)
            assert isinstance(result, ValidationResponse)
            assert result.success is False
