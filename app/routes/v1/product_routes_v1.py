from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from app.schemas import ProductSchema, ProductUpdateSchema, ProductErrorExamples
from app.services import get_all_products, create_new_product, update_product, get_product_by_id, ValidationResponse
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

    @product_bp.response(200, ProductSchema(many=True))
    def get(self):
        """Retrieve all products"""
        products_data = get_all_products()
        if products_data is None:
            return jsonify({"success":False,"message":"Data is empty"}),400
        
        return jsonify({"success":True,"message":"get all products successful","data":products_data}),200

    @product_bp.doc(responses=ProductErrorExamples.RESPONSES_POST_PRODUCT,security=[{"BearerAuth": []}])
    @product_bp.arguments(ProductSchema, location="json")
    @roles_required('SELLER', 'ADMIN', 'SUPERADMIN')
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

    @product_bp.response(200, ProductSchema)
    def get(self, id):
        """Retrieve product detail by ID"""
        product = get_product_by_id(id)

        if not product:
            abort(404, message="Product is not found")

        return jsonify({"success": True, "message": "get product detail successful", "data": product.to_dict()}), 200

    @product_bp.doc(security=[{"BearerAuth": []}])
    @product_bp.arguments(ProductUpdateSchema, location="json")
    @roles_required('SELLER', 'ADMIN', 'SUPERADMIN')
    @product_bp.response(200, ProductSchema)
    def put(self, update_data, id):
        """Update a product by ID"""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()

        product = update_product(id, update_data, jwt_user_id, roles)

        if isinstance(product, ValidationResponse):
            abort(400, message=product.message)

        if product:
            return jsonify({"success": True, "message": "Product updated successfully", "data": product.to_dict()}), 200
        else:
            return jsonify({"success": False, "message": "Failed to update product"}), 400
