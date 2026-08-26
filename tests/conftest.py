"""
Test configuration — uses a separate PostgreSQL test database.
Auto-creates '{your_db_name}_test' from your .env SQLALCHEMY_DATABASE_URI.
Your production data is NEVER touched.
"""
import pytest
import os
from dotenv import load_dotenv

load_dotenv()

from flask_jwt_extended import create_access_token


def _get_test_db_uri():
    """Derive test DB URI by appending '_test' to the production DB name."""
    prod_uri = os.environ.get('SQLALCHEMY_DATABASE_URI', '')
    if '/' in prod_uri:
        base, db_name = prod_uri.rsplit('/', 1)
        return f"{base}/{db_name}_test"
    return prod_uri + '_test'


def _ensure_test_db_exists(uri):
    """Create the test database if it doesn't exist."""
    import sqlalchemy
    base, db_name = uri.rsplit('/', 1)
    engine = sqlalchemy.create_engine(f"{base}/postgres", isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        result = conn.execute(sqlalchemy.text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
        if not result.fetchone():
            conn.execute(sqlalchemy.text(f"CREATE DATABASE {db_name}"))
    engine.dispose()


# Setup test DB URI
TEST_DB_URI = _get_test_db_uri()
os.environ['SQLALCHEMY_DATABASE_URI'] = TEST_DB_URI
_ensure_test_db_exists(TEST_DB_URI)

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    """Create Flask app pointing to the test database."""
    test_app = create_app()
    test_app.config['TESTING'] = True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DB_URI
    test_app.config['JWT_SECRET_KEY'] = 'test-secret'
    test_app.config['TAX_PERCENT'] = 11.0
    test_app.config['CURRENCY'] = 'IDR'

    with test_app.app_context():
        _db.drop_all()
        _db.create_all()

    yield test_app

    with test_app.app_context():
        _db.drop_all()


@pytest.fixture(scope='function')
def db_session(app):
    """Provide a transactional session that rolls back after each test."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        _db.session.bind = connection
        yield _db.session
        _db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(app, db_session):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def buyer_headers(app):
    with app.app_context():
        token = create_access_token(identity='1', additional_claims={'roles': ['BUYER']})
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def seller_headers(app):
    with app.app_context():
        token = create_access_token(identity='2', additional_claims={'roles': ['SELLER']})
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def admin_headers(app):
    with app.app_context():
        token = create_access_token(identity='3', additional_claims={'roles': ['ADMIN']})
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def superadmin_headers(app):
    with app.app_context():
        token = create_access_token(identity='4', additional_claims={'roles': ['SUPERADMIN']})
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
