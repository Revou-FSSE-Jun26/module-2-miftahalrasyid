"""Integration tests for auth_service — real DB operations."""
from unittest.mock import patch, MagicMock
from app.models import User
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token, decode_token
from app.services.auth_service import (
    register_user,
    login_user,
    oauth_google_login,
    confirm_email,
    generate_token,
    generate_email_confirmation_token,
    send_verification_email,
)
from app.services.user_service import ValidationResponse
import hashlib


class TestGenerateToken:
    def test_returns_string(self, app, db_session):
        user = User(username='tokenuser', email='tokenuser@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = generate_token(user)
        assert isinstance(token, str)
        assert len(token) > 10


class TestRegisterUser:
    @patch('app.services.auth_service.send_verification_email')
    def test_register_success(self, mock_email, app, db_session):
        mock_email.return_value = True
        result = register_user('newreg@gmail.com', 'password123', 20)
        assert 'access_token' in result
        assert result['email'] == 'newreg@gmail.com'
        assert result['is_active'] is False

    @patch('app.services.auth_service.send_verification_email')
    def test_register_duplicate_email(self, mock_email, app, db_session):
        mock_email.return_value = True
        register_user('dupreg@gmail.com', 'password123', 20)
        result = register_user('dupreg@gmail.com', 'password456', 22)
        assert isinstance(result, ValidationResponse)
        assert 'already registered' in result.message

    def test_register_invalid_email(self, app, db_session):
        result = register_user('not-an-email', 'password123', 20)
        assert isinstance(result, ValidationResponse)
        assert 'Email format' in result.message


class TestLoginUser:
    @patch('app.services.auth_service.send_verification_email')
    def test_login_success(self, mock_email, app, db_session):
        mock_email.return_value = True
        # Create an active user
        user = User(username='loginuser', email='loginuser@gmail.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('mypass123'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = login_user('loginuser@gmail.com', 'mypass123')
        assert 'access_token' in result
        assert result['message'] == 'Login successful.'

    def test_login_invalid_email(self, app, db_session):
        result = login_user('bad-email', 'pass')
        assert isinstance(result, ValidationResponse)
        assert 'Invalid email or password' in result.message

    def test_login_wrong_password(self, app, db_session):
        user = User(username='wrongpw', email='wrongpw@gmail.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('correctpass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = login_user('wrongpw@gmail.com', 'wrongpass')
        assert isinstance(result, ValidationResponse)
        assert 'Invalid email or password' in result.message

    def test_login_user_not_found(self, app, db_session):
        result = login_user('nobody@gmail.com', 'pass123')
        assert isinstance(result, ValidationResponse)

    def test_login_inactive_user(self, app, db_session):
        user = User(username='inactive', email='inactive@gmail.com', age=25, is_active=False,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass123'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = login_user('inactive@gmail.com', 'pass123')
        assert isinstance(result, ValidationResponse)
        assert 'verify your email' in result.message

    def test_login_oauth_user_with_password(self, app, db_session):
        user = User(username='oauthuser', email='oauthuser@gmail.com', age=25, is_active=True,
            provider=AuthProvider.GOOGLE_OAUTH, provider_key='google-sub-id',
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = login_user('oauthuser@gmail.com', 'anypass')
        assert isinstance(result, ValidationResponse)
        assert 'Google OAuth' in result.message

    def test_login_soft_deleted_user(self, app, db_session):
        from sqlalchemy import func
        user = User(username='deleted', email='deleted@gmail.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass123'),
            roles=[UserRole.BUYER])
        user.deleted_at = func.now()
        db_session.add(user)
        db_session.commit()
        result = login_user('deleted@gmail.com', 'pass123')
        assert isinstance(result, ValidationResponse)
        assert 'deactivated' in result.message

    def test_login_sha256_legacy_works(self, app, db_session):
        """Test backward compat: SHA256 hash login succeeds."""
        legacy_hash = hashlib.sha256('legacypass'.encode('utf-8')).hexdigest()
        user = User(username='legacyuser', email='legacyuser@gmail.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=legacy_hash,
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = login_user('legacyuser@gmail.com', 'legacypass')
        assert 'access_token' in result
        assert result['message'] == 'Login successful.'


class TestOAuthGoogleLogin:
    @patch('app.services.auth_service.google_id_token.verify_oauth2_token')
    def test_oauth_new_user(self, mock_verify, app, db_session):
        mock_verify.return_value = {
            'email': 'googlenew@gmail.com',
            'sub': 'google-sub-123',
            'name': 'Google User'
        }
        result = oauth_google_login('fake-token', 25)
        assert 'access_token' in result
        assert result['email'] == 'googlenew@gmail.com'
        assert result['is_active'] is True

    @patch('app.services.auth_service.google_id_token.verify_oauth2_token')
    def test_oauth_existing_user(self, mock_verify, app, db_session):
        user = User(username='existoauth', email='existoauth@gmail.com', age=25, is_active=True,
            provider=AuthProvider.GOOGLE_OAUTH, provider_key='existing-sub',
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        mock_verify.return_value = {
            'email': 'existoauth@gmail.com',
            'sub': 'existing-sub',
            'name': 'Exist User'
        }
        result = oauth_google_login('fake-token', 25)
        assert 'access_token' in result
        assert 'Login successful via Google' in result['message']

    @patch('app.services.auth_service.google_id_token.verify_oauth2_token')
    def test_oauth_invalid_token(self, mock_verify, app, db_session):
        mock_verify.side_effect = ValueError("Invalid token")
        result = oauth_google_login('bad-token', 25)
        assert isinstance(result, ValidationResponse)
        assert 'invalid or expired' in result.message

    @patch('app.services.auth_service.google_id_token.verify_oauth2_token')
    def test_oauth_deactivated_user(self, mock_verify, app, db_session):
        from sqlalchemy import func
        user = User(username='deactoauth', email='deactoauth@gmail.com', age=25, is_active=True,
            provider=AuthProvider.GOOGLE_OAUTH, provider_key='deact-sub',
            roles=[UserRole.BUYER])
        user.deleted_at = func.now()
        db_session.add(user)
        db_session.commit()
        mock_verify.return_value = {
            'email': 'deactoauth@gmail.com',
            'sub': 'deact-sub',
            'name': 'Deact User'
        }
        result = oauth_google_login('fake-token', 25)
        assert isinstance(result, ValidationResponse)
        assert 'deactivated' in result.message

    @patch('app.services.auth_service.google_id_token.verify_oauth2_token')
    def test_oauth_no_email_in_token(self, mock_verify, app, db_session):
        mock_verify.return_value = {'sub': 'no-email-sub', 'name': 'No Email'}
        result = oauth_google_login('fake-token', 25)
        assert isinstance(result, ValidationResponse)
        assert 'email' in result.message.lower()


class TestConfirmEmail:
    def test_confirm_valid_token(self, app, db_session):
        user = User(username='confirmuser', email='confirmuser@gmail.com', age=25, is_active=False,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = generate_email_confirmation_token(user)
        result = confirm_email(token)
        assert result['is_active'] is True
        assert 'verified successfully' in result['message']

    def test_confirm_already_active(self, app, db_session):
        user = User(username='alreadyactive', email='alreadyactive@gmail.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        token = generate_email_confirmation_token(user)
        result = confirm_email(token)
        assert 'already verified' in result['message']

    def test_confirm_invalid_token(self, app, db_session):
        result = confirm_email('invalid-token-string')
        assert isinstance(result, ValidationResponse)
        assert 'invalid or has expired' in result.message

    def test_confirm_wrong_purpose(self, app, db_session):
        user = User(username='wrongpurpose', email='wrongpurpose@gmail.com', age=25, is_active=False,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        # Create a normal access token (no "purpose" claim)
        token = create_access_token(identity=str(user.id), additional_claims={'roles': ['BUYER']})
        result = confirm_email(token)
        assert isinstance(result, ValidationResponse)


class TestSendVerificationEmail:
    @patch('app.services.auth_service.smtplib.SMTP_SSL')
    def test_send_email_success(self, mock_smtp, app, db_session):
        import os
        os.environ['EMAIL_USER'] = 'test@gmail.com'
        os.environ['EMAIL_PASS'] = 'testpass'
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        user = User(username='emailuser', email='emailuser@gmail.com', age=25, is_active=False,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = send_verification_email(user)
        assert result is True

    def test_send_email_no_config(self, app, db_session):
        import os
        os.environ.pop('EMAIL_USER', None)
        os.environ.pop('EMAIL_PASS', None)
        user = User(username='noconfig', email='noconfig@gmail.com', age=25, is_active=False,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('pass'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = send_verification_email(user)
        assert result is False
