from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from app.schemas import CategorySchema, CategoryUpdateSchema, DeleteActionSchema
from app.services import get_all_categories, get_category_by_id, create_category, update_category, delete_category, ValidationResponse
from app.models import UserRole
from app.services.auth_service import roles_required
from app.permissions.field_filter import get_allowed_fields
from flask_jwt_extended import get_jwt

category_bp = Blueprint(
    'categories',
    __name__,
    url_prefix='/api/v1/categories',
    description='Category Data Operations'
)


@category_bp.route('/')
class CategoriesRoot(MethodView):

    @category_bp.doc(responses={
        "400": {"description": "Business logic validation failed"},
    })
    @category_bp.response(200, CategorySchema(many=True))
    def get(self):
        """Retrieve all categories. Supports ?page=1&per_page=10 (max 30)."""
        result = get_all_categories()
        if result is None:
            return jsonify({"success": False, "message": "Failed to retrieve categories"}), 400

        # Default read fields for unauthenticated users (same as buyer)
        allowed = {"name", "created_at"}

        try:
            jwt_data = get_jwt()
            if jwt_data and jwt_data.get("roles"):
                roles = jwt_data["roles"]
                allowed = get_allowed_fields("categories", roles, "read_list")
        except Exception:
            pass

        data = [
            {k: v for k, v in cat.__dict__.items() if k in allowed and not k.startswith('_')}
            for cat in result["items"]
        ]

        return jsonify({
            "success": True,
            "message": "Get all categories successful",
            "data": data,
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            }
        }), 200

    @category_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Business logic validation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "422": {"description": "Input validation failed"},
    })
    @category_bp.arguments(CategorySchema, location="json")
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @category_bp.response(201, CategorySchema)
    def post(self, category_instance):
        """Create a new category (admin/superadmin only)"""
        roles = get_jwt()['roles']

        result = create_category(category_instance, roles)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        if result:
            return jsonify({"success": True, "message": "Category created successfully", "data": {"id": result.id, "name": result.name, "created_at": str(result.created_at), "deleted_at": str(result.deleted_at) if result.deleted_at else None}}), 201
        else:
            return jsonify({"success": False, "message": "Failed to create category"}), 400


@category_bp.route('/<int:id>')
class CategoryDetail(MethodView):

    @category_bp.doc(responses={
        "404": {"description": "Resource not found"},
    })
    @category_bp.response(200, CategorySchema)
    def get(self, id):
        """Retrieve category detail by ID"""
        category = get_category_by_id(id)

        if not category:
            abort(404, message="Category not found")

        # Default read fields for unauthenticated users (same as buyer)
        allowed = {"id", "name", "created_at"}

        try:
            jwt_data = get_jwt()
            if jwt_data and jwt_data.get("roles"):
                roles = jwt_data["roles"]
                allowed = get_allowed_fields("categories", roles, "read")
        except Exception:
            pass

        data = {k: v for k, v in category.__dict__.items() if k in allowed and not k.startswith('_')}
        # Serialize datetime fields
        for key in ("created_at", "deleted_at"):
            if key in data and data[key] is not None:
                data[key] = str(data[key])

        return jsonify({"success": True, "message": "Get category detail successful", "data": data}), 200

    @category_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Business logic validation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
        "422": {"description": "Input validation failed"},
    })
    @category_bp.arguments(CategoryUpdateSchema, location="json")
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @category_bp.response(200, CategorySchema)
    def put(self, update_data, id):
        """Update a category by ID."""
        roles = get_jwt()['roles']

        result = update_category(id, update_data, roles)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        if result:
            return jsonify({"success": True, "message": "Category updated successfully", "data": {"id": result.id, "name": result.name, "created_at": str(result.created_at), "deleted_at": str(result.deleted_at) if result.deleted_at else None}}), 200
        else:
            return jsonify({"success": False, "message": "Failed to update category"}), 400

    @category_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Delete operation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
    })
    @category_bp.arguments(DeleteActionSchema, location="json")
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @category_bp.response(200, CategorySchema)
    def delete(self, delete_data, id):
        """Delete a category by ID. Default=soft delete. Superadmin can pass {"action":"hard"}."""
        roles = get_jwt()['roles']
        action = delete_data.get("action", "soft")

        result = delete_category(id, roles, action)

        if not result.success:
            return jsonify({"success": False, "message": result.message}), result.status_code

        return jsonify({"success": True, "message": result.message}), result.status_code


@category_bp.route('/<int:id>/products')
class CategoryProducts(MethodView):

    @category_bp.doc(responses={
        "404": {"description": "Resource not found"},
    })
    @category_bp.response(200, CategorySchema)
    def get(self, id):
        """Get all active products under a specific category (public)."""
        from app.models import Product, Category
        from app.utils.pagination import paginate_query

        category = get_category_by_id(id)
        if not category:
            abort(404, message="Category not found")

        query = Product.query.filter(
            Product.deleted_at.is_(None),
            Product.is_active == True,
            Product.categories.any(Category.id == id)
        )

        result = paginate_query(query)

        return jsonify({
            "success": True,
            "message": f"Products in category '{category.name}'",
            "data": [p.to_dict() for p in result["items"]],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            }
        }), 200
