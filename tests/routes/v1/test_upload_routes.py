"""Route tests for uploads — mock service layer."""
from unittest.mock import patch
from app.services import ValidationResponse
import io


class TestUpload:
    def test_no_auth(self, client):
        resp = client.post('/api/v1/uploads/')
        assert resp.status_code == 401

    def test_buyer_forbidden(self, client, buyer_headers):
        resp = client.post('/api/v1/uploads/', headers=buyer_headers)
        assert resp.status_code == 403

    @patch('app.routes.v1.upload_routes_v1.upload_image')
    def test_missing_resource(self, mock_svc, client, seller_headers):
        resp = client.post('/api/v1/uploads/', data={}, headers=seller_headers, content_type='multipart/form-data')
        assert resp.status_code == 400

    @patch('app.routes.v1.upload_routes_v1.upload_image')
    def test_success(self, mock_svc, client, seller_headers):
        mock_svc.return_value = {'success': True, 'message': 'Uploaded', 'image_path': 'products/uuid/img.png', 'total_images': 1}
        data = {'resource': 'products', 'resource_id': '1', 'file': (io.BytesIO(b'\x89PNG\r\n'), 'test.png')}
        resp = client.post('/api/v1/uploads/', data=data, headers=seller_headers, content_type='multipart/form-data')
        assert resp.status_code == 201


class TestDeleteUpload:
    def test_no_auth(self, client):
        resp = client.delete('/api/v1/uploads/', json={})
        assert resp.status_code == 401

    @patch('app.routes.v1.upload_routes_v1.delete_image')
    def test_success(self, mock_svc, client, seller_headers):
        mock_svc.return_value = {'success': True, 'message': 'Deleted'}
        resp = client.delete('/api/v1/uploads/', json={'resource': 'products', 'resource_id': 1, 'filename': 'test.png'}, headers=seller_headers)
        assert resp.status_code == 200
