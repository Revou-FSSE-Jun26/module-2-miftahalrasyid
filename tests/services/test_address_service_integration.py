"""Integration tests for address_service — real DB operations."""
from app.models import User, Address
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from app.services.address_service import (
    get_addresses_by_user, get_address_by_id, create_address,
    update_address, delete_address, MAX_ADDRESSES_PER_USER
)
from app.services import ValidationResponse


class TestGetAddressesByUser:
    def test_returns_list(self, app, db_session):
        user = User(username='addrget', email='addrget@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        a1 = Address(user_id=user.id, label='Home', recipient_name='T', phone='+6281234567890',
            address_line='St1', city='C', province='P', postal_code='1', is_default=True)
        a2 = Address(user_id=user.id, label='Office', recipient_name='T', phone='+6281234567890',
            address_line='St2', city='C', province='P', postal_code='2', is_default=False)
        db_session.add_all([a1, a2])
        db_session.commit()
        result = get_addresses_by_user(user.id)
        assert len(result) == 2

    def test_empty(self, app, db_session):
        user = User(username='addrempty', email='addrempty@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = get_addresses_by_user(user.id)
        assert result == []


class TestGetAddressById:
    def test_found(self, app, db_session):
        user = User(username='addrbyid', email='addrbyid@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(user_id=user.id, label='Home', recipient_name='T', phone='+6281234567890',
            address_line='St', city='C', province='P', postal_code='1', is_default=True)
        db_session.add(addr)
        db_session.commit()
        result = get_address_by_id(addr.id, user.id)
        assert result is not None
        assert result.label == 'Home'

    def test_not_found(self, app, db_session):
        result = get_address_by_id(99999, 1)
        assert result is None

    def test_wrong_user(self, app, db_session):
        user = User(username='addrwrong', email='addrwrong@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(user_id=user.id, label='Mine', recipient_name='T', phone='+6281234567890',
            address_line='St', city='C', province='P', postal_code='1', is_default=True)
        db_session.add(addr)
        db_session.commit()
        result = get_address_by_id(addr.id, 99999)
        assert result is None


class TestCreateAddress:
    def test_first_address_default(self, app, db_session):
        user = User(username='addrfirst', email='addrfirst@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(label='Home', recipient_name='T', phone='+6281234567890',
            address_line='St', city='C', province='P', postal_code='1', is_default=False)
        result = create_address(user.id, addr)
        assert result.is_default is True

    def test_second_address_not_default(self, app, db_session):
        user = User(username='addrsecond', email='addrsecond@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        a1 = Address(user_id=user.id, label='First', recipient_name='T', phone='+6281234567890',
            address_line='St', city='C', province='P', postal_code='1', is_default=True)
        db_session.add(a1)
        db_session.commit()
        addr = Address(label='Second', recipient_name='T', phone='+6281234567890',
            address_line='St2', city='C', province='P', postal_code='2', is_default=False)
        result = create_address(user.id, addr)
        assert result.is_default is False

    def test_max_addresses_limit(self, app, db_session):
        user = User(username='addrmax', email='addrmax@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        for i in range(MAX_ADDRESSES_PER_USER):
            a = Address(user_id=user.id, label=f'Addr{i}', recipient_name='T', phone='+6281234567890',
                address_line=f'St{i}', city='C', province='P', postal_code=str(i), is_default=(i==0))
            db_session.add(a)
        db_session.commit()
        addr = Address(label='Extra', recipient_name='T', phone='+6281234567890',
            address_line='StX', city='C', province='P', postal_code='X', is_default=False)
        result = create_address(user.id, addr)
        assert isinstance(result, ValidationResponse)
        assert 'Maximum' in result.message

    def test_set_as_default_unsets_others(self, app, db_session):
        user = User(username='addrdef', email='addrdef@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        a1 = Address(user_id=user.id, label='Old', recipient_name='T', phone='+6281234567890',
            address_line='St', city='C', province='P', postal_code='1', is_default=True)
        db_session.add(a1)
        db_session.commit()
        addr = Address(label='New Default', recipient_name='T', phone='+6281234567890',
            address_line='St2', city='C', province='P', postal_code='2', is_default=True)
        result = create_address(user.id, addr)
        assert result.is_default is True
        db_session.refresh(a1)
        assert a1.is_default is False


class TestUpdateAddress:
    def test_success(self, app, db_session):
        user = User(username='addrupdsvc', email='addrupdsvc@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(user_id=user.id, label='Old', recipient_name='T', phone='+6281234567890',
            address_line='St', city='Jakarta', province='DKI', postal_code='1', is_default=True)
        db_session.add(addr)
        db_session.commit()
        result = update_address(addr.id, user.id, {'city': 'Bandung'})
        assert result.city == 'Bandung'

    def test_not_found(self, app, db_session):
        result = update_address(99999, 1, {'city': 'Ghost'})
        assert isinstance(result, ValidationResponse)
        assert 'not found' in result.message

    def test_set_default(self, app, db_session):
        user = User(username='addrdefupd', email='addrdefupd@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        a1 = Address(user_id=user.id, label='A1', recipient_name='T', phone='+6281234567890',
            address_line='St1', city='C', province='P', postal_code='1', is_default=True)
        a2 = Address(user_id=user.id, label='A2', recipient_name='T', phone='+6281234567890',
            address_line='St2', city='C', province='P', postal_code='2', is_default=False)
        db_session.add_all([a1, a2])
        db_session.commit()
        result = update_address(a2.id, user.id, {'is_default': True})
        assert result.is_default is True
        db_session.refresh(a1)
        assert a1.is_default is False


class TestDeleteAddress:
    def test_success(self, app, db_session):
        user = User(username='addrdelsvc', email='addrdelsvc@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(user_id=user.id, label='Del', recipient_name='T', phone='+6281234567890',
            address_line='St', city='C', province='P', postal_code='1', is_default=True)
        db_session.add(addr)
        db_session.commit()
        result = delete_address(addr.id, user.id)
        assert result.success is True

    def test_not_found(self, app, db_session):
        result = delete_address(99999, 1)
        assert isinstance(result, ValidationResponse)
        assert 'not found' in result.message

    def test_default_promoted(self, app, db_session):
        user = User(username='addrpromote', email='addrpromote@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        a1 = Address(user_id=user.id, label='Default', recipient_name='T', phone='+6281234567890',
            address_line='St1', city='C', province='P', postal_code='1', is_default=True)
        a2 = Address(user_id=user.id, label='Other', recipient_name='T', phone='+6281234567890',
            address_line='St2', city='C', province='P', postal_code='2', is_default=False)
        db_session.add_all([a1, a2])
        db_session.commit()
        result = delete_address(a1.id, user.id)
        assert result.success is True
        db_session.refresh(a2)
        assert a2.is_default is True
