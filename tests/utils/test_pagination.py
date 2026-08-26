"""Unit tests for pagination utility — pure Python."""
from unittest.mock import patch, MagicMock


class TestPaginateQuery:
    def test_defaults(self, app):
        with app.test_request_context('/?page=1&per_page=10'):
            from app.utils.pagination import paginate_query
            mock_query = MagicMock()
            mock_pagination = MagicMock()
            mock_pagination.items = []
            mock_pagination.page = 1
            mock_pagination.per_page = 10
            mock_pagination.total = 0
            mock_pagination.pages = 0
            mock_query.paginate.return_value = mock_pagination
            result = paginate_query(mock_query)
            assert result['page'] == 1
            assert result['per_page'] == 10
            assert result['count'] == 0

    def test_max_per_page_enforced(self, app):
        with app.test_request_context('/?page=1&per_page=100'):
            from app.utils.pagination import paginate_query
            mock_query = MagicMock()
            mock_pagination = MagicMock()
            mock_pagination.items = []
            mock_pagination.page = 1
            mock_pagination.per_page = 30
            mock_pagination.total = 0
            mock_pagination.pages = 0
            mock_query.paginate.return_value = mock_pagination
            result = paginate_query(mock_query, max_per_page=30)
            mock_query.paginate.assert_called_once_with(page=1, per_page=30, error_out=False)

    def test_page_less_than_1_defaults_to_1(self, app):
        with app.test_request_context('/?page=-5&per_page=10'):
            from app.utils.pagination import paginate_query
            mock_query = MagicMock()
            mock_pagination = MagicMock()
            mock_pagination.items = ['a', 'b']
            mock_pagination.page = 1
            mock_pagination.per_page = 10
            mock_pagination.total = 2
            mock_pagination.pages = 1
            mock_query.paginate.return_value = mock_pagination
            result = paginate_query(mock_query)
            assert result['count'] == 2
