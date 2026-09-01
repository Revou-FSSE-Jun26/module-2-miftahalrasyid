from app.models import Category
from app.extensions import db
from app.services import ValidationResponse


class TestCreateCategory:
    def test_success(self, app, db_session):
        
            cat = Category(name='test_cat_new')
            from app.services.category_service import create_category
            result = create_category(cat, ['ADMIN'])
            assert result is not None
            assert result.name == 'test_cat_new'

    def test_no_permission(self, app, db_session):
        
            cat = Category(name='blocked')
            from app.services.category_service import create_category
            result = create_category(cat, ['BUYER'])
            assert isinstance(result, ValidationResponse)

    def test_duplicate_name(self, app, db_session):
        """Creating a category with an existing name hits the IntegrityError branch."""
        from app.services.category_service import create_category
        first = Category(name='dupe_cat')
        result1 = create_category(first, ['ADMIN'])
        assert result1 is not None
        # Second with same name -> unique violation
        second = Category(name='dupe_cat')
        result2 = create_category(second, ['ADMIN'])
        assert isinstance(result2, ValidationResponse)
        assert 'already exists' in result2.message


class TestDeleteCategory:
    def test_not_found(self, app, db_session):
        
            from app.services.category_service import delete_category
            result = delete_category(9999, ['ADMIN'], 'soft')
            assert result.success is False
            assert result.status_code == 404

    def test_soft_delete(self, app, db_session):
        
            cat = Category(name='to_delete_cat')
            db_session.add(cat)
            db_session.commit()
            from app.services.category_service import delete_category
            result = delete_category(cat.id, ['ADMIN'], 'soft')
            assert result.success is True


class TestGetAllCategories:
    def test_returns_paginated(self, app, db_session, client):
        db_session.add(Category(name='svc_cat_a'))
        db_session.add(Category(name='svc_cat_b'))
        db_session.commit()
        resp = client.get('/api/v1/categories/')
        assert resp.status_code == 200
        assert resp.get_json()['pagination']['total'] >= 2


class TestGetCategoryById:
    def test_found(self, app, db_session):
        cat = Category(name='find_me')
        db_session.add(cat)
        db_session.commit()
        from app.services.category_service import get_category_by_id
        result = get_category_by_id(cat.id)
        assert result is not None
        assert result.name == 'find_me'

    def test_not_found(self, app, db_session):
        from app.services.category_service import get_category_by_id
        result = get_category_by_id(99999)
        assert result is None


class TestUpdateCategory:
    def test_success(self, app, db_session):
        cat = Category(name='upd_cat')
        db_session.add(cat)
        db_session.commit()
        from app.services.category_service import update_category
        result = update_category(cat.id, {'name': 'upd_cat_new'}, ['ADMIN'])
        assert result.name == 'upd_cat_new'

    def test_not_found(self, app, db_session):
        from app.services.category_service import update_category
        result = update_category(99999, {'name': 'ghost'}, ['ADMIN'])
        assert isinstance(result, ValidationResponse)
        assert 'not found' in result.message

    def test_no_permission(self, app, db_session):
        cat = Category(name='upd_blocked')
        db_session.add(cat)
        db_session.commit()
        from app.services.category_service import update_category
        result = update_category(cat.id, {'name': 'new'}, ['BUYER'])
        assert isinstance(result, ValidationResponse)
        assert 'permission' in result.message

    def test_duplicate_name_on_update(self, app, db_session):
        """Updating a category to a name that already exists hits the IntegrityError branch."""
        from app.services.category_service import update_category
        existing = Category(name='taken_name')
        target = Category(name='rename_me')
        db_session.add_all([existing, target])
        db_session.commit()
        result = update_category(target.id, {'name': 'taken_name'}, ['ADMIN'])
        assert isinstance(result, ValidationResponse)
        assert 'already exists' in result.message


class TestDeleteCategoryExtra:
    def test_hard_delete_superadmin(self, app, db_session):
        cat = Category(name='hard_del_cat')
        db_session.add(cat)
        db_session.commit()
        from app.services.category_service import delete_category
        result = delete_category(cat.id, ['SUPERADMIN'], 'hard')
        assert result.success is True
        assert 'permanently' in result.message

    def test_hard_delete_admin_blocked(self, app, db_session):
        cat = Category(name='blocked_hard')
        db_session.add(cat)
        db_session.commit()
        from app.services.category_service import delete_category
        result = delete_category(cat.id, ['ADMIN'], 'hard')
        assert result.success is False
        assert result.status_code == 403

    def test_no_permission_buyer(self, app, db_session):
        cat = Category(name='buyer_del')
        db_session.add(cat)
        db_session.commit()
        from app.services.category_service import delete_category
        result = delete_category(cat.id, ['BUYER'], 'soft')
        assert result.success is False
        assert result.status_code == 403

    def test_already_deleted(self, app, db_session):
        from sqlalchemy import func
        cat = Category(name='already_del')
        cat.deleted_at = func.now()
        db_session.add(cat)
        db_session.commit()
        from app.services.category_service import delete_category
        result = delete_category(cat.id, ['ADMIN'], 'soft')
        assert result.success is False
        assert 'already deleted' in result.message
