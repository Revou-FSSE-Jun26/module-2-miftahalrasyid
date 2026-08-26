from app.models import User
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from app.services import ValidationResponse


class TestDeleteUser:
    def test_soft_delete(self, app, db_session):
        
            user = User(username='del_user', email='del_user@test.com', age=25, is_active=True,
                provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
                roles=[UserRole.BUYER])
            db_session.add(user)
            db_session.commit()
            from app.services.user_service import delete_user
            result = delete_user(user.id, ['ADMIN'], 'soft')
            assert result.success is True
            assert result.status_code == 200

    def test_not_found(self, app, db_session):
        
            from app.services.user_service import delete_user
            result = delete_user(99999, ['ADMIN'], 'soft')
            assert result.success is False
            assert result.status_code == 404

    def test_no_permission(self, app, db_session):
        
            from app.services.user_service import delete_user
            result = delete_user(1, ['BUYER'], 'soft')
            assert result.success is False


class TestNormalizeEmail:
    def test_gmail_strips_dots(self, app):
        
            from app.services.user_service import normalize_and_validate_email
            result = normalize_and_validate_email('test.user@gmail.com')
            assert result == 'testuser@gmail.com'

    def test_gmail_strips_plus(self, app):
        
            from app.services.user_service import normalize_and_validate_email
            result = normalize_and_validate_email('test+spam@gmail.com')
            assert result == 'test@gmail.com'

    def test_invalid_email(self, app):
        
            from app.services.user_service import normalize_and_validate_email
            result = normalize_and_validate_email('notanemail')
            assert result is None


class TestGetAllUsers:
    def test_returns_paginated(self, app, db_session, client):
        u1 = User(username='svc_u1', email='svc_u1@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        u2 = User(username='svc_u2', email='svc_u2@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add_all([u1, u2])
        db_session.commit()
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(u1.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get('/api/v1/users/', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['pagination']['total'] >= 2


class TestGetUserBy:
    def test_found(self, app, db_session):
        user = User(username='findme', email='findme@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        from app.services.user_service import get_user_by
        result = get_user_by(user.id)
        assert result is not None
        assert result.username == 'findme'

    def test_not_found(self, app, db_session):
        from app.services.user_service import get_user_by
        result = get_user_by(99999)
        assert result is None


class TestUpdateUserBy:
    def test_updates_age(self, app, db_session):
        user = User(username='updage', email='updage@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        from app.services.user_service import update_user_by
        from unittest.mock import MagicMock
        update_obj = MagicMock()
        update_obj.age = 30
        update_obj.provider_key = None
        update_obj.roles = None
        update_obj.is_active = None
        result = update_user_by(user.id, update_obj, ['BUYER'])
        assert result.age == 30

    def test_not_found(self, app, db_session):
        from app.services.user_service import update_user_by
        from unittest.mock import MagicMock
        update_obj = MagicMock()
        update_obj.age = 30
        update_obj.provider_key = None
        update_obj.roles = None
        update_obj.is_active = None
        result = update_user_by(99999, update_obj, ['ADMIN'])
        assert isinstance(result, ValidationResponse)

    def test_admin_updates_roles(self, app, db_session):
        user = User(username='rolesupd', email='rolesupd@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        from app.services.user_service import update_user_by
        from unittest.mock import MagicMock
        update_obj = MagicMock()
        update_obj.age = None
        update_obj.provider_key = None
        update_obj.roles = ['BUYER', 'SELLER']
        update_obj.is_active = None
        result = update_user_by(user.id, update_obj, ['ADMIN'])
        assert UserRole.SELLER in result.roles


class TestBecomeSeller:
    def test_success(self, app, db_session):
        user = User(username='becomesell', email='becomesell@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        from app.services.user_service import become_seller
        result = become_seller(user.id)
        assert UserRole.SELLER in result.roles

    def test_already_seller(self, app, db_session):
        user = User(username='alrseller', email='alrseller@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER, UserRole.SELLER])
        db_session.add(user)
        db_session.commit()
        from app.services.user_service import become_seller
        result = become_seller(user.id)
        assert isinstance(result, ValidationResponse)
        assert 'already a seller' in result.message

    def test_deactivated_user(self, app, db_session):
        from sqlalchemy import func
        user = User(username='deactsell', email='deactsell@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        user.deleted_at = func.now()
        db_session.add(user)
        db_session.commit()
        from app.services.user_service import become_seller
        result = become_seller(user.id)
        assert isinstance(result, ValidationResponse)
        assert 'deactivated' in result.message

    def test_user_not_found(self, app, db_session):
        from app.services.user_service import become_seller
        result = become_seller(99999)
        assert isinstance(result, ValidationResponse)


class TestAddNewUsers:
    def test_success(self, app, db_session):
        from app.services.user_service import add_new_users
        user = User(email='newuser@gmail.com', age=25,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        result = add_new_users(user)
        assert result.username == 'newuser'

    def test_invalid_email(self, app, db_session):
        from app.services.user_service import add_new_users
        user = User(email='bademail', age=25,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        result = add_new_users(user)
        assert isinstance(result, ValidationResponse)
        assert 'Email format' in result.message

    def test_duplicate_email(self, app, db_session):
        from app.services.user_service import add_new_users
        user1 = User(username='dup1', email='dupnew@gmail.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user1)
        db_session.commit()
        user2 = User(email='dupnew@gmail.com', age=30,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        result = add_new_users(user2)
        assert isinstance(result, ValidationResponse)
        assert 'already registered' in result.message


class TestDeleteUserExtra:
    def test_hard_delete_superadmin(self, app, db_session):
        user = User(username='harddelusr', email='harddelusr@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        from app.services.user_service import delete_user
        result = delete_user(user.id, ['SUPERADMIN'], 'hard')
        assert result.success is True
        assert 'permanently' in result.message

    def test_hard_delete_admin_blocked(self, app, db_session):
        user = User(username='hardblocku', email='hardblocku@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        from app.services.user_service import delete_user
        result = delete_user(user.id, ['ADMIN'], 'hard')
        assert result.success is False
        assert result.status_code == 403

    def test_already_deleted(self, app, db_session):
        from sqlalchemy import func
        user = User(username='alrdelu', email='alrdelu@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        user.deleted_at = func.now()
        db_session.add(user)
        db_session.commit()
        from app.services.user_service import delete_user
        result = delete_user(user.id, ['ADMIN'], 'soft')
        assert result.success is False
        assert 'already deactivated' in result.message
