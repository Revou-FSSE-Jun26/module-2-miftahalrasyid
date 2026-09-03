from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from app.schemas import ProductSchema, ProductUpdateSchema, ProductErrorExamples, DeleteActionSchema, ProductQueryArgs
from app.services import get_all_products, create_new_product, update_product, get_product_by_id, delete_product, ValidationResponse
from app.models import Category, UserRole
from app.services.auth_service import roles_required
from flask_jwt_extended import get_jwt_identity, get_jwt

product_bp = Blueprint(
    'products',
    __name__,
    url_prefix='/api/v1/products',
    description='Product Data Operations'
)


@product_bp.route('/')
class ProductsRoot(MethodView):

    @product_bp.doc(responses={
        "400": {"description": "Business logic validation failed"},
    })
    @product_bp.arguments(ProductQueryArgs, location="query")
    @product_bp.response(200, ProductSchema(many=True))
    def get(self, query_args):
        """Retrieve all products. Supports pagination, search, category/price filters and sorting."""
        result = get_all_products(query_args)
        if result is None:
            return jsonify({"success": False, "message": "Failed to retrieve products"}), 400
        
        return jsonify({
            "success": True,
            "message": "get all products successful",
            "data": [p.to_dict() for p in result["items"]],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            }
        }), 200

    @product_bp.doc(responses={
        **ProductErrorExamples.RESPONSES_POST_PRODUCT,
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "422": {"description": "Input validation failed"},
    }, security=[{"BearerAuth": []}])
    @product_bp.arguments(ProductSchema, location="json")
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @product_bp.response(201, ProductSchema)
    def post(self, product_instance):
        """Add a new product"""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()
        
        # Call service with user_id (integer) and product_instance (SQLAlchemy Model)
        product = create_new_product(jwt_user_id, product_instance, roles)
        if isinstance(product, ValidationResponse):
            abort(400, messages=product.message)
        # Handle success/failure
        if product:
            return jsonify({"success": True, "message": "Product created successfully", "data": product.to_dict()}), 201
        else:
            return jsonify({"success": False, "message": "Failed to create product"}), 400


@product_bp.route('/<int:id>')
class ProductDetail(MethodView):

    @product_bp.doc(responses={
        "404": {"description": "Resource not found"},
    })
    @product_bp.response(200, ProductSchema)
    def get(self, id):
        """Retrieve product detail by ID"""
        product = get_product_by_id(id)

        if not product:
            abort(404, message="Product is not found")

        return jsonify({"success": True, "message": "get product detail successful", "data": product.to_dict()}), 200

    @product_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Business logic validation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
        "422": {"description": "Input validation failed"},
    })
    @product_bp.arguments(ProductUpdateSchema, location="json")
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @product_bp.response(200, ProductSchema)
    def put(self, update_data, id):
        """Update a product by ID."""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()

        # Normal update flow
        product = update_product(id, update_data, jwt_user_id, roles)

        if isinstance(product, ValidationResponse):
            abort(400, message=product.message)

        if product:
            return jsonify({"success": True, "message": "Product updated successfully", "data": product.to_dict()}), 200
        else:
            return jsonify({"success": False, "message": "Failed to update product"}), 400

    @product_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Delete operation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
    })
    @product_bp.arguments(DeleteActionSchema, location="json")
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @product_bp.response(200, ProductSchema)
    def delete(self, delete_data, id):
        """Delete a product by ID. Default=soft delete. Superadmin can pass {"action":"hard"}."""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()
        action = delete_data.get("action", "soft")

        result = delete_product(id, jwt_user_id, roles, action)

        if not result.success:
            return jsonify({"success": False, "message": result.message}), result.status_code

        return jsonify({"success": True, "message": result.message}), result.status_code
