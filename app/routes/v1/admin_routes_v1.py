from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from app.models import Product, Order, UserRole
from app.models.order_items_model import Order_item
from app.models.user_model import User
from app.services.auth_service import roles_required
from app.services.order_service import get_order_items
from app.utils.pagination import paginate_query
from flask_jwt_extended import get_jwt

admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/api/v1/admin',
    description='Admin Operations'
)


@admin_bp.route('/products')
class AdminProducts(MethodView):

    @admin_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
    })
    @admin_bp.response(200)
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self):
        """Get all products including inactive and soft-deleted (admin/superadmin only). Paginated."""
        query = Product.query
        result = paginate_query(query)

        return jsonify({
            "success": True,
            "message": "All products (admin view)",
            "data": [p.to_dict() for p in result["items"]],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            }
        }), 200


@admin_bp.route('/users/<int:user_id>/orders')
class AdminUserOrders(MethodView):

    @admin_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
    })
    @admin_bp.response(200)
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, user_id):
        """Get all orders for a specific user (admin/superadmin only). Paginated."""
        user = User.query.get(user_id)
        if not user:
            abort(404, message="User not found")

        query = Order.query.filter(Order.user_id == user_id)
        result = paginate_query(query)

        data = []
        for order in result["items"]:
            order_dict = order.to_dict()
            order_dict["items"] = get_order_items(order.id)
            data.append(order_dict)

        return jsonify({
            "success": True,
            "message": f"Orders for user {user_id}",
            "data": data,
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            }
        }), 200


@admin_bp.route('/orders/<int:order_id>/products')
class AdminOrderProducts(MethodView):

    @admin_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
    })
    @admin_bp.response(200)
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, order_id):
        """Get full product details for all items in any order (admin/superadmin only)."""
        order = Order.query.filter(Order.id == order_id).first()
        if not order:
            abort(404, message="Order not found")

        items = Order_item.query.filter(
            Order_item.order_id == order_id,
            Order_item.deleted_at.is_(None)
        ).all()

        products_data = []
        for item in items:
            product = Product.query.get(item.product_id)
            if product:
                product_info = product.to_dict()
                product_info["quantity"] = item.quantity
                product_info["compound_price"] = float(item.compound_price)
                products_data.append(product_info)

        return jsonify({
            "success": True,
            "message": f"Products in order {order_id} (admin view)",
            "data": products_data
        }), 200


@admin_bp.route('/users/<int:user_id>/profile')
class AdminUserProfile(MethodView):

    @admin_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
    })
    @admin_bp.response(200)
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, user_id):
        """Get a user's profile (admin/superadmin only)."""
        from app.models.profile_model import Profile

        user = User.query.get(user_id)
        if not user:
            abort(404, message="User not found")

        profile = Profile.query.filter_by(user_id=user_id).first()

        return jsonify({
            "success": True,
            "message": f"Profile for user {user_id}",
            "data": profile.to_dict() if profile else None
        }), 200


@admin_bp.route('/users/<int:user_id>/addresses')
class AdminUserAddresses(MethodView):

    @admin_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
    })
    @admin_bp.response(200)
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, user_id):
        """Get all addresses for a user (admin/superadmin only)."""
        from app.models.address_model import Address

        user = User.query.get(user_id)
        if not user:
            abort(404, message="User not found")

        addresses = Address.query.filter_by(user_id=user_id).all()

        return jsonify({
            "success": True,
            "message": f"Addresses for user {user_id}",
            "data": [addr.to_dict() for addr in addresses]
        }), 200


@admin_bp.route('/categories/<int:category_id>/products')
class AdminCategoryProducts(MethodView):

    @admin_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
    })
    @admin_bp.response(200)
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, category_id):
        """Get all products in a category including inactive/deleted (admin/superadmin only). Paginated."""
        from app.models.category_model import Category

        category = Category.query.get(category_id)
        if not category:
            abort(404, message="Category not found")

        query = Product.query.filter(
            Product.categories.any(Category.id == category_id)
        )
        result = paginate_query(query)

        return jsonify({
            "success": True,
            "message": f"All products in category '{category.name}' (admin view)",
            "data": [p.to_dict() for p in result["items"]],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            }
        }), 200
