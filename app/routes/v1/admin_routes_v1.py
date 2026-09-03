from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from app.models import Product, Order, UserRole
from app.models.order_items_model import Order_item
from app.models.user_model import User
from app.services.auth_service import roles_required
from app.services.order_service import get_order_items
from app.utils.pagination import paginate_query
from app.schemas import AdminProductQueryArgs, AdminOrderQueryArgs
from flask_jwt_extended import get_jwt
from sqlalchemy import asc, desc

admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/api/v1/admin',
    description='Admin Operations'
)


def _apply_admin_product_filters(query, args):
    """Apply search/category/price/is_active/include_deleted/sort filters for admin product listings."""
    from app.models.category_model import Category

    args = args or {}

    search = args.get("search")
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    category_id = args.get("category_id")
    if category_id:
        query = query.filter(Product.categories.any(Category.id == category_id))

    min_price = args.get("min_price")
    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    max_price = args.get("max_price")
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    is_active = args.get("is_active")
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    # Admin view includes soft-deleted by default; allow opting out.
    if args.get("include_deleted") is False:
        query = query.filter(Product.deleted_at.is_(None))

    sort = args.get("sort")
    sort_columns = {"price": Product.price, "name": Product.name, "created_at": Product.created_at}
    if sort:
        column = sort_columns.get(sort.lstrip("-"))
        if column is not None:
            query = query.order_by(desc(column) if sort.startswith("-") else asc(column))
    else:
        query = query.order_by(Product.id.asc())

    return query


def _apply_admin_order_filters(query, args):
    """Apply status/sort filters for admin order listings."""
    from app.models.order_model import OrderStatus

    args = args or {}

    status = args.get("status")
    if status:
        try:
            query = query.filter(Order.status == OrderStatus(status))
        except ValueError:
            pass

    sort = args.get("sort")
    sort_columns = {"total": Order.total, "created_at": Order.created_at}
    if sort:
        column = sort_columns.get(sort.lstrip("-"))
        if column is not None:
            query = query.order_by(desc(column) if sort.startswith("-") else asc(column))
    else:
        query = query.order_by(Order.id.asc())

    return query


@admin_bp.route('/products')
class AdminProducts(MethodView):

    @admin_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
    })
    @admin_bp.arguments(AdminProductQueryArgs, location="query")
    @admin_bp.response(200)
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, query_args):
        """Get all products including inactive and soft-deleted (admin/superadmin only). Supports pagination, search, filters and sorting."""
        query = _apply_admin_product_filters(Product.query, query_args)
        result = paginate_query(query, args=query_args)

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
    @admin_bp.arguments(AdminOrderQueryArgs, location="query")
    @admin_bp.response(200)
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, query_args, user_id):
        """Get all orders for a specific user (admin/superadmin only). Supports pagination, status filter and sorting."""
        user = User.query.get(user_id)
        if not user:
            abort(404, message="User not found")

        query = _apply_admin_order_filters(Order.query.filter(Order.user_id == user_id), query_args)
        result = paginate_query(query, args=query_args)

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
    @admin_bp.arguments(AdminProductQueryArgs, location="query")
    @admin_bp.response(200)
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, query_args, category_id):
        """Get all products in a category including inactive/deleted (admin/superadmin only). Supports pagination, filters and sorting."""
        from app.models.category_model import Category

        category = Category.query.get(category_id)
        if not category:
            abort(404, message="Category not found")

        # category scoping comes from the path param; drop any category_id filter.
        scoped_args = dict(query_args or {})
        scoped_args.pop("category_id", None)
        query = Product.query.filter(Product.categories.any(Category.id == category_id))
        query = _apply_admin_product_filters(query, scoped_args)
        result = paginate_query(query, args=query_args)

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
