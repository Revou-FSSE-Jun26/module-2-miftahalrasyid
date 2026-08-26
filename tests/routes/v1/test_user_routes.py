"""Route tests for users — mock service layer."""
from unittest.mock import patch, MagicMock


class TestGetUserPublic:
    @patch('app.routes.v1.users_routes_v1.get_user_by')
    def test_returns_username_only(self, mock_svc, client):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_svc.return_value = mock_user
        resp = client.get('/api/v1/users/1')
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert 'username' in data
        assert 'email' not in data

    @patch('app.routes.v1.users_routes_v1.get_user_by')
    def test_not_found(self, mock_svc, client):
        mock_svc.return_value = None
        resp = client.get('/api/v1/users/999')
        assert resp.status_code == 404


class TestGetMe:
    def test_no_auth(self, client):
        resp = client.get('/api/v1/users/me')
        assert resp.status_code == 401

    @patch('app.routes.v1.users_routes_v1.get_profile_by_user_id')
    @patch('app.routes.v1.users_routes_v1.get_user_by')
    def test_authenticated(self, mock_user, mock_profile, client, buyer_headers):
        mock_u = MagicMock()
        mock_u.id = 1
        mock_u.username = 'buyer'
        mock_u.email = 'buyer@test.com'
        mock_u.age = 25
        mock_u.roles = []
        mock_u.is_active = True
        mock_u.provider = MagicMock(value='PASSWORD_HASH')
        mock_u.created_at = None
        mock_user.return_value = mock_u
        mock_profile.return_value = None
        resp = client.get('/api/v1/users/me', headers=buyer_headers)
        assert resp.status_code == 200


class TestAddresses:
    def test_get_addresses_no_auth(self, client):
        resp = client.get('/api/v1/users/me/addresses')
        assert resp.status_code == 401

    @patch('app.services.address_service.get_addresses_by_user')
    def test_get_addresses_success(self, mock_svc, client, buyer_headers):
        mock_svc.return_value = []
        resp = client.get('/api/v1/users/me/addresses', headers=buyer_headers)
        assert resp.status_code == 200

    def test_post_address_no_auth(self, client):
        resp = client.post('/api/v1/users/me/addresses', json={})
        assert resp.status_code == 401


# --- Integration tests using test DB ---
from app.models import User, Profile, Address
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token


class TestGetMeIntegration:
    def test_get_me_returns_profile(self, app, db_session, client):
        user = User(username='meuser', email='meuser@test.com', age=28, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        profile = Profile(user_id=user.id, bio='Hello', phone='+6281234567890')
        db_session.add(profile)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        resp = client.get('/api/v1/users/me', headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert data['username'] == 'meuser'
        assert data['profile']['bio'] == 'Hello'


class TestAddressesIntegration:
    def test_create_address(self, app, db_session, client):
        user = User(username='addruser', email='addruser@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/users/me/addresses', headers=headers, json={
            'label': 'Home', 'recipient_name': 'Test User', 'phone': '+6281234567890',
            'address_line': '123 Test St', 'city': 'Jakarta', 'province': 'DKI Jakarta', 'postal_code': '12345'
        })
        assert resp.status_code == 201
        assert resp.get_json()['data']['is_default'] is True

    def test_get_addresses(self, app, db_session, client):
        user = User(username='getaddr', email='getaddr@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(user_id=user.id, label='Office', recipient_name='T', phone='+6281234567890',
            address_line='456 St', city='Bandung', province='Jabar', postal_code='40000', is_default=True)
        db_session.add(addr)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get('/api/v1/users/me/addresses', headers=headers)
        assert resp.status_code == 200
        assert len(resp.get_json()['data']) == 1

    def test_invalid_phone_rejected(self, app, db_session, client):
        user = User(username='badphone', email='badphone@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/users/me/addresses', headers=headers, json={
            'label': 'Home', 'recipient_name': 'T', 'phone': '12345',
            'address_line': 'St', 'city': 'C', 'province': 'P', 'postal_code': '1'
        })
        assert resp.status_code == 422


class TestBecomeSeller:
    def test_buyer_becomes_seller(self, app, db_session, client):
        user = User(username='wannasell', email='wannasell@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/users/become-seller', headers=headers)
        assert resp.status_code == 200


class TestUserUpdateIntegration:
    def test_user_updates_own_age(self, app, db_session, client):
        user = User(username='ageuser', email='ageuser@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.put(f'/api/v1/users/{user.id}', headers=headers, json={'age': 30})
        assert resp.status_code == 200

    def test_user_updates_own_password(self, app, db_session, client):
        user = User(username='pwduser', email='pwduser@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('oldpass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.put(f'/api/v1/users/{user.id}', headers=headers, json={'password': 'newpass123'})
        assert resp.status_code == 200

    def test_user_cannot_update_another(self, app, db_session, client):
        user1 = User(username='self1', email='self1@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        user2 = User(username='other1', email='other1@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add_all([user1, user2])
        db_session.commit()
        token = create_access_token(identity=str(user1.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.put(f'/api/v1/users/{user2.id}', headers=headers, json={'age': 99})
        assert resp.status_code == 403

    def test_admin_updates_user_roles(self, app, db_session, client):
        target = User(username='target1', email='target1@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        admin = User(username='adminupd', email='adminupd@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add_all([target, admin])
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.put(f'/api/v1/users/{target.id}', headers=headers, json={'roles': ['BUYER', 'SELLER']})
        assert resp.status_code == 200


class TestUserDeleteIntegration:
    def test_admin_soft_deletes_user(self, app, db_session, client):
        target = User(username='deltarget', email='deltarget@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        admin = User(username='deladmin', email='deladmin@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add_all([target, admin])
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/users/{target.id}', headers=headers, json={})
        assert resp.status_code == 200

    def test_superadmin_hard_deletes_user(self, app, db_session, client):
        target = User(username='hardtarget', email='hardtarget@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        sa = User(username='delsa', email='delsa@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SUPERADMIN])
        db_session.add_all([target, sa])
        db_session.commit()
        token = create_access_token(identity=str(sa.id), additional_claims={'roles': ['SUPERADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/users/{target.id}', headers=headers, json={'action': 'hard'})
        assert resp.status_code == 200

    def test_delete_user_not_found(self, app, db_session, client):
        admin = User(username='delnf', email='delnf@test.com', age=35, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.ADMIN])
        db_session.add(admin)
        db_session.commit()
        token = create_access_token(identity=str(admin.id), additional_claims={'roles': ['ADMIN']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete('/api/v1/users/99999', headers=headers, json={})
        assert resp.status_code == 404


class TestGetAllUsersIntegration:
    def test_returns_users(self, app, db_session, client):
        u1 = User(username='allusr1', email='allusr1@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        u2 = User(username='allusr2', email='allusr2@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add_all([u1, u2])
        db_session.commit()
        token = create_access_token(identity=str(u1.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get('/api/v1/users/', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['pagination']['total'] >= 2


class TestProfileUpdateIntegration:
    def test_update_profile(self, app, db_session, client):
        user = User(username='profupd', email='profupd@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        profile = Profile(user_id=user.id, bio='Old bio')
        db_session.add(profile)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.put('/api/v1/users/me/profile', headers=headers, json={
            'bio': 'New bio', 'phone': '+6281234567890'
        })
        assert resp.status_code == 200
        assert resp.get_json()['data']['bio'] == 'New bio'


class TestAddressDetailIntegration:
    def test_get_address_by_id(self, app, db_session, client):
        user = User(username='addrdet', email='addrdet@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(user_id=user.id, label='Home', recipient_name='T', phone='+6281234567890',
            address_line='123 St', city='Jakarta', province='DKI', postal_code='12345', is_default=True)
        db_session.add(addr)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get(f'/api/v1/users/me/addresses/{addr.id}', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['label'] == 'Home'

    def test_update_address(self, app, db_session, client):
        user = User(username='addrupd', email='addrupd@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(user_id=user.id, label='Office', recipient_name='T', phone='+6281234567890',
            address_line='456 St', city='Bandung', province='Jabar', postal_code='40000', is_default=True)
        db_session.add(addr)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.put(f'/api/v1/users/me/addresses/{addr.id}', headers=headers, json={
            'label': 'Main Office', 'city': 'Surabaya'
        })
        assert resp.status_code == 200
        assert resp.get_json()['data']['city'] == 'Surabaya'

    def test_delete_address(self, app, db_session, client):
        user = User(username='addrdel', email='addrdel@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        addr = Address(user_id=user.id, label='Temp', recipient_name='T', phone='+6281234567890',
            address_line='789 St', city='Medan', province='Sumut', postal_code='20000', is_default=True)
        db_session.add(addr)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.delete(f'/api/v1/users/me/addresses/{addr.id}', headers=headers)
        assert resp.status_code == 200

    def test_address_not_found(self, app, db_session, client):
        user = User(username='addrnf', email='addrnf@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.get('/api/v1/users/me/addresses/99999', headers=headers)
        assert resp.status_code == 404
