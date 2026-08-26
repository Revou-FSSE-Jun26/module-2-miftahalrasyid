"""Integration tests for auth routes — real DB operations."""
from unittest.mock import patch
from app.models import User
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from app.services.auth_service import generate_email_confirmation_token


class TestAuthRegisterRoute:
    @patch('app.services.auth_service.send_verification_email')
    def test_register_success(self, mock_email, app, db_session, client):
        mock_email.return_value = True
        resp = client.post('/api/v1/auth/register', json={
            'email': 'routereg@gmail.com', 'password': 'pass123456', 'age': 20
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'access_token' in data

    @patch('app.services.auth_service.send_verification_email')
    def test_register_duplicate(self, mock_email, app, db_session, client):
        mock_email.return_value = True
        client.post('/api/v1/auth/register', json={
            'email': 'routedup@gmail.com', 'password': 'pass123456', 'age': 20
        })
        resp = client.post('/api/v1/auth/register', json={
            'email': 'routedup@gmail.com', 'password': 'pass789', 'age': 22
        })
        assert resp.status_code == 400

    def test_register_invalid_email(self, app, db_session, client):
        resp = client.post('/api/v1/auth/register', json={
            'email': 'not-valid', 'password': 'pass123456', 'age': 20
        })
        assert resp.status_code == 422

    def test_register_missing_password(self, app, db_session, client):
        resp = client.post('/api/v1/auth/register', json={
            'email': 'test@gmail.com', 'age': 20
        })
        assert resp.status_code == 422

    def test_register_underage(self, app, db_session, client):
        resp = client.post('/api/v1/auth/register', json={
            'email': 'young@gmail.com', 'password': 'pass123456', 'age': 15
        })
        assert resp.status_code == 422

    def test_register_short_password(self, app, db_session, client):
        resp = client.post('/api/v1/auth/register', json={
            'email': 'short@gmail.com', 'password': '12345', 'age': 20
        })
        assert resp.status_code == 422


class TestAuthLoginRoute:
    def test_login_success(self, app, db_session, client):
        user = User(username='loginroute', email='loginroute@gmail.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('mypass123'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        resp = client.post('/api/v1/auth/login', json={
            'email': 'loginroute@gmail.com', 'password': 'mypass123'
        })
        assert resp.status_code == 200
        assert 'access_token' in resp.get_json()

    def test_login_wrong_password(self, app, db_session, client):
        user = User(username='loginwrong', email='loginwrong@gmail.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('correct'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        resp = client.post('/api/v1/auth/login', json={
            'email': 'loginwrong@gmail.com', 'password': 'incorrect'
        })
        assert resp.status_code == 400

    def test_login_nonexistent_user(self, app, db_session, client):
        resp = client.post('/api/v1/auth/login', json={
            'email': 'ghost@gmail.com', 'password': 'pass123'
        })
        assert resp.status_code == 400

    def test_login_missing_fields(self, app, db_session, client):
        resp = client.post('/api/v1/auth/login', json={'email': 'test@gmail.com'})
        assert resp.status_code == 422


class TestAuthOAuthRoute:
    @patch('app.services.auth_service.google_id_token.verify_oauth2_token')
    def test_oauth_success(self, mock_verify, app, db_session, client):
        mock_verify.return_value = {
            'email': 'oauthroute@gmail.com', 'sub': 'oauth-sub-1', 'name': 'OAuth User'
        }
        resp = client.post('/api/v1/auth/oauth/google', json={
            'id_token': 'fake-google-token', 'age': 25
        })
        assert resp.status_code == 200
        assert 'access_token' in resp.get_json()

    @patch('app.services.auth_service.google_id_token.verify_oauth2_token')
    def test_oauth_invalid_token(self, mock_verify, app, db_session, client):
        mock_verify.side_effect = ValueError("Bad token")
        resp = client.post('/api/v1/auth/oauth/google', json={
            'id_token': 'bad-token', 'age': 25
        })
        assert resp.status_code == 400

    def test_oauth_missing_token(self, app, db_session, client):
        resp = client.post('/api/v1/auth/oauth/google', json={'age': 25})
        assert resp.status_code == 422

    def test_oauth_underage(self, app, db_session, client):
        resp = client.post('/api/v1/auth/oauth/google', json={
            'id_token': 'token', 'age': 15
        })
        assert resp.status_code == 422


class TestEmailConfirmationRoute:
    def test_confirm_success(self, app, db_session, client):
        user = User(username='confirmrt', email='confirmrt@gmail.com', age=25, is_active=False,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = generate_email_confirmation_token(user)
        resp = client.get(f'/api/v1/auth/email_confirmation?token={token}')
        assert resp.status_code == 200
        assert resp.get_json()['is_active'] is True

    def test_confirm_missing_token(self, app, db_session, client):
        resp = client.get('/api/v1/auth/email_confirmation')
        assert resp.status_code == 400

    def test_confirm_invalid_token(self, app, db_session, client):
        resp = client.get('/api/v1/auth/email_confirmation?token=garbage')
        assert resp.status_code == 400
