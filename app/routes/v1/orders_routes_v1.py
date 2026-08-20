from flask.views import MethodView
from flask import jsonify, request
from flask_smorest import Blueprint, abort
from app.schemas import OrderSchema, OrderUpdateSchema, DeleteActionSchema, OrderItemSchema, OrderErrorExamples
from app.services.order_service import get_all_orders, get_order_by_id, create_order, update_order, delete_order, get_order_items
from app.services import ValidationResponse
from app.models import UserRole
from app.services.auth_service import roles_required
from app.permissions.field_filter import get_allowed_fields
from flask_jwt_extended import get_jwt_identity, get_jwt

order_bp = Blueprint(
    'orders',
    __name__,
    url_prefix='/api/v1/orders',
    description='Order Data Operations'
)


@order_bp.route('/')
class OrdersRoot(MethodView):

    @order_bp.doc(security=[{"BearerAuth": []}])
    @order_bp.response(200, OrderSchema(many=True))
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self):
        """Retrieve orders (filtered by role: buyer=own, seller=their products, admin=all)"""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()

        orders = get_all_orders(jwt_user_id, roles)
        if orders is None:
            return jsonify({"success": False, "message": "Failed to retrieve orders"}), 400

        # Filter fields by role
        allowed = get_allowed_fields("orders", roles, "read")
        data = []
        for order in orders:
            order_dict = order.to_dict()
            filtered = {k: v for k, v in order_dict.items() if k in allowed}
            # Include items summary
            filtered["items"] = get_order_items(order.id)
            data.append(filtered)

        return jsonify({"success": True, "message": "Get orders successful", "data": data}), 200

    @order_bp.doc(security=[{"BearerAuth": []}])
    @order_bp.arguments(OrderSchema, location="json")
    @roles_required(UserRole.BUYER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @order_bp.response(201, OrderSchema)
    def post(self, order_instance):
        """Create a new order with items. Body: {"name": "...", "items": [{"product_id": 1, "quantity": 2}]}"""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()

        # Get items from raw request (schema strips them via load_only)
        raw_data = request.get_json(silent=True) or {}
        items_data = raw_data.get("items", [])

        result = create_order(order_instance, items_data, jwt_user_id, roles)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        if result:
            order_dict = result.to_dict()
            order_dict["items"] = get_order_items(result.id)
            return jsonify({"success": True, "message": "Order created successfully", "data": order_dict}), 201
        else:
            return jsonify({"success": False, "message": "Failed to create order"}), 400


@order_bp.route('/<int:id>')
class OrderDetail(MethodView):

    @order_bp.doc(security=[{"BearerAuth": []}])
    @order_bp.response(200, OrderSchema)
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, id):
        """Retrieve order detail by ID (with ownership/role check)"""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()

        order = get_order_by_id(id, jwt_user_id, roles)
        if not order:
            abort(404, message="Order not found")

        allowed = get_allowed_fields("orders", roles, "read")
        order_dict = order.to_dict()
        filtered = {k: v for k, v in order_dict.items() if k in allowed}
        filtered["items"] = get_order_items(order.id)

        return jsonify({"success": True, "message": "Get order detail successful", "data": filtered}), 200

    @order_bp.doc(security=[{"BearerAuth": []}])
    @order_bp.arguments(OrderUpdateSchema, location="json")
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @order_bp.response(200, OrderSchema)
    def put(self, update_data, id):
        """Update an order (status transition). Seller can advance status for orders with their products."""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()

        result = update_order(id, update_data, jwt_user_id, roles)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        if result:
            order_dict = result.to_dict()
            order_dict["items"] = get_order_items(result.id)
            return jsonify({"success": True, "message": "Order updated successfully", "data": order_dict}), 200
        else:
            return jsonify({"success": False, "message": "Failed to update order"}), 400

    @order_bp.doc(security=[{"BearerAuth": []}])
    @order_bp.arguments(DeleteActionSchema, location="json")
    @roles_required(UserRole.BUYER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @order_bp.response(200, OrderSchema)
    def delete(self, delete_data, id):
        """Delete/cancel an order. Buyer can cancel own PENDING orders. Admin=soft, Superadmin can hard."""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()
        action = delete_data.get("action", "soft")

        result = delete_order(id, jwt_user_id, roles, action)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        if result:
            return jsonify({"success": True, "message": result["message"]}), 200
        else:
            return jsonify({"success": False, "message": "Failed to delete order"}), 400
