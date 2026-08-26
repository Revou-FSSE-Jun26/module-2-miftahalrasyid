"""Integration tests for upload_service — real DB operations."""
import os
import io
from unittest.mock import patch, MagicMock
from app.models import User, Product
from app.models.user_model import UserRole, AuthProvider
from app.extensions import db
from werkzeug.security import generate_password_hash
from werkzeug.datastructures import FileStorage
from decimal import Decimal
from app.services.upload_service import (
    upload_image, delete_image, _allowed_file, _get_extension,
    UPLOAD_ROOT, MAX_IMAGES_PER_PRODUCT
)
from app.services import ValidationResponse


class TestHelpers:
    def test_allowed_file_valid(self, app):
        assert _allowed_file('photo.png') is True
        assert _allowed_file('img.jpg') is True
        assert _allowed_file('pic.jpeg') is True
        assert _allowed_file('banner.webp') is True

    def test_allowed_file_invalid(self, app):
        assert _allowed_file('doc.pdf') is False
        assert _allowed_file('script.exe') is False
        assert _allowed_file('noext') is False

    def test_get_extension(self, app):
        assert _get_extension('photo.png') == 'png'
        assert _get_extension('file.tar.gz') == 'gz'
        assert _get_extension('noext') == ''


class TestUploadImage:
    def test_no_permission_buyer(self, app, db_session):
        result = upload_image('products', 1, None, '1', ['BUYER'])
        assert isinstance(result, ValidationResponse)
        assert 'permission' in result.message

    def test_no_file_provided(self, app, db_session):
        result = upload_image('products', 1, None, '1', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'No file' in result.message

    def test_empty_filename(self, app, db_session):
        file = FileStorage(stream=io.BytesIO(b'data'), filename='')
        result = upload_image('products', 1, file, '1', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'No file' in result.message

    def test_invalid_extension(self, app, db_session):
        file = FileStorage(stream=io.BytesIO(b'data'), filename='doc.pdf')
        result = upload_image('products', 1, file, '1', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'Invalid file type' in result.message

    def test_file_too_large(self, app, db_session):
        big_data = b'x' * (3 * 1024 * 1024)  # 3MB
        file = FileStorage(stream=io.BytesIO(big_data), filename='big.png')
        result = upload_image('products', 1, file, '1', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'exceeds' in result.message

    def test_product_not_found(self, app, db_session):
        file = FileStorage(stream=io.BytesIO(b'imgdata'), filename='test.png')
        result = upload_image('products', 99999, file, '1', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'not found' in result.message

    def test_not_owner(self, app, db_session):
        seller = User(username='uplseller', email='uplseller@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='UplProd', slug='uplprod', uuid='upluuid1',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        file = FileStorage(stream=io.BytesIO(b'imgdata'), filename='test.png')
        result = upload_image('products', prod.id, file, '9999', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'own products' in result.message

    def test_upload_success(self, app, db_session):
        seller = User(username='uplok', email='uplok@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='UplOk', slug='uplok', uuid='uplokuuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True)
        db_session.add(prod)
        db_session.commit()
        file = FileStorage(stream=io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100), filename='photo.png')
        result = upload_image('products', prod.id, file, str(seller.id), ['SELLER'])
        assert result['success'] is True
        assert 'image_path' in result
        # Cleanup: remove file and the uuid directory
        file_path = os.path.join(UPLOAD_ROOT, result['image_path'])
        if os.path.exists(file_path):
            os.remove(file_path)
        uuid_dir = os.path.join(UPLOAD_ROOT, 'products', prod.uuid)
        if os.path.isdir(uuid_dir) and not os.listdir(uuid_dir):
            os.rmdir(uuid_dir)

    def test_max_images_reached(self, app, db_session):
        seller = User(username='uplmax', email='uplmax@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='UplMax', slug='uplmax', uuid='uplmaxuuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True,
            images=['img1.png', 'img2.png', 'img3.png', 'img4.png'])
        db_session.add(prod)
        db_session.commit()
        file = FileStorage(stream=io.BytesIO(b'imgdata'), filename='extra.png')
        result = upload_image('products', prod.id, file, str(seller.id), ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'Maximum' in result.message

    def test_unsupported_resource_permission_denied(self, app, db_session):
        """Even SELLER can't upload to 'orders' — blocked at RBAC level."""
        file = FileStorage(stream=io.BytesIO(b'imgdata'), filename='test.png')
        result = upload_image('orders', 1, file, '1', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'permission' in result.message


class TestDeleteImage:
    def test_no_permission_buyer(self, app, db_session):
        result = delete_image('products', 1, 'test.png', '1', ['BUYER'])
        assert isinstance(result, ValidationResponse)
        assert 'permission' in result.message

    def test_product_not_found(self, app, db_session):
        result = delete_image('products', 99999, 'test.png', '1', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'not found' in result.message

    def test_not_owner(self, app, db_session):
        seller = User(username='delseller', email='delseller@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='DelProd', slug='delprod-upl', uuid='deluuid1',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True,
            images=['products/deluuid1/test.png'])
        db_session.add(prod)
        db_session.commit()
        result = delete_image('products', prod.id, 'test.png', '9999', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'own products' in result.message

    def test_image_not_in_list(self, app, db_session):
        seller = User(username='delnoimg', email='delnoimg@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='NoImg', slug='noimg', uuid='noimguuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True,
            images=[])
        db_session.add(prod)
        db_session.commit()
        result = delete_image('products', prod.id, 'ghost.png', str(seller.id), ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'not found' in result.message

    def test_delete_success(self, app, db_session):
        seller = User(username='delok', email='delok@test.com', age=30, is_active=True,
            provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
            roles=[UserRole.SELLER])
        db_session.add(seller)
        db_session.commit()
        prod = Product(user_id=seller.id, name='DelOk', slug='delok', uuid='delokuuid',
            stock=10, brand='B', description='D', price=Decimal('100'), is_active=True,
            images=['products/delokuuid/delok_photo.png'])
        db_session.add(prod)
        db_session.commit()
        # Create the file so delete can succeed
        folder = os.path.join(UPLOAD_ROOT, 'products', 'delokuuid')
        os.makedirs(folder, exist_ok=True)
        fpath = os.path.join(folder, 'delok_photo.png')
        with open(fpath, 'wb') as f:
            f.write(b'fake image data')
        result = delete_image('products', prod.id, 'delok_photo.png', str(seller.id), ['SELLER'])
        assert result['success'] is True
        assert not os.path.exists(fpath)
        # Cleanup folder
        if os.path.exists(folder):
            os.rmdir(folder)

    def test_unsupported_resource(self, app, db_session):
        result = delete_image('orders', 1, 'test.png', '1', ['SELLER'])
        assert isinstance(result, ValidationResponse)
        assert 'not supported' in result.message
