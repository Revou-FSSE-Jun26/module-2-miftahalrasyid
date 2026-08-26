"""Integration tests for profile_service — real DB operations."""
from app.models import User, Profile
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from app.services.profile_service import get_profile_by_user_id, create_profile, update_profile
from app.services import ValidationResponse


class TestGetProfileByUserId:
    def test_returns_profile(self, app, db_session):
        user = User(username='profget', email='profget@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        profile = Profile(user_id=user.id, bio='Test bio')
        db_session.add(profile)
        db_session.commit()
        result = get_profile_by_user_id(user.id)
        assert result is not None
        assert result.bio == 'Test bio'

    def test_returns_none_when_no_profile(self, app, db_session):
        user = User(username='noprof', email='noprof@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = get_profile_by_user_id(user.id)
        assert result is None


class TestCreateProfile:
    def test_creates_empty_profile(self, app, db_session):
        user = User(username='newprof', email='newprof@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        result = create_profile(user.id)
        assert result is not None
        assert result.user_id == user.id

    def test_returns_existing_if_exists(self, app, db_session):
        user = User(username='existprof', email='existprof@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        profile = Profile(user_id=user.id, bio='Existing')
        db_session.add(profile)
        db_session.commit()
        result = create_profile(user.id)
        assert result.bio == 'Existing'


class TestUpdateProfile:
    def test_updates_bio(self, app, db_session):
        user = User(username='updprof', email='updprof@test.com', age=25, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.BUYER])
        db_session.add(user)
        db_session.commit()
        profile = Profile(user_id=user.id, bio='Old bio')
        db_session.add(profile)
        db_session.commit()
        result = update_profile(user.id, {'bio': 'New bio', 'phone': '+6281234567890'})
        assert result.bio == 'New bio'
        assert result.phone == '+6281234567890'

    def test_profile_not_found(self, app, db_session):
        result = update_profile(99999, {'bio': 'No profile'})
        assert isinstance(result, ValidationResponse)
        assert 'not found' in result.message.lower()
