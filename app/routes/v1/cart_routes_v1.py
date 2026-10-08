from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from app.schemas import CartItemAddSchema, CartItemUpdateSchema, CartItemSchema, CartQueryArgs, DeleteActionSchema
from app.services.cart_service import (
    get_cart,
    add_to_cart,
    update_cart_item,
    remove_cart_item,
    clear_cart,
)
from app.services import ValidationResponse
from app.models import UserRole
from app.services.auth_service import roles_required
from flask_jwt_extended import get_jwt_identity

cart_bp = Blueprint(
    'cart',
    __name__,
    url_prefix='/api/v1/cart',
    description='Shopping Cart Operations (per-user, private)',
)

# Buyers and sellers both own a cart. Sellers can buy from other sellers; the
# service still blocks adding their own listing. Admin/superadmin do not shop.
_CART_ROLES = (UserRole.BUYER.value, UserRole.SELLER.value)


@cart_bp.route('/')
class CartRoot(MethodView):

    @cart_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
    })
    @cart_bp.arguments(CartQueryArgs, location="query")
    @cart_bp.response(200, CartItemSchema(many=True))
    @roles_required(*_CART_ROLES)
    def get(self, query_args):
        """Get the caller's cart (live prices/stock + summary)."""
        jwt_user_id = get_jwt_identity()

        result = get_cart(jwt_user_id, query_args)
        if result is None:
            return jsonify({"success": False, "message": "Failed to retrieve cart"}), 400

        return jsonify({
            "success": True,
            "message": "Get cart successful",
            "data": result["items"],
            "summary": result["summary"],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            },
        }), 200

    @cart_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Business logic validation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "422": {"description": "Input validation failed"},
    })
    @cart_bp.arguments(DeleteActionSchema, location="json", required=False)
    @roles_required(*_CART_ROLES)
    @cart_bp.response(200)
    def delete(self, _delete_data):
        """Empty the caller's cart."""
        jwt_user_id = get_jwt_identity()
        result = clear_cart(jwt_user_id)
        return jsonify({"success": result.success, "message": result.message}), result.status_code


@cart_bp.route('/items')
class CartItems(MethodView):

    @cart_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Business logic validation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "422": {"description": "Input validation failed"},
    })
    @cart_bp.arguments(CartItemAddSchema, location="json")
    @roles_required(*_CART_ROLES)
    @cart_bp.response(201, CartItemSchema)
    def post(self, data):
        """Add a listing to the cart. Re-adding bumps quantity (stock-capped)."""
        jwt_user_id = get_jwt_identity()

        result = add_to_cart(jwt_user_id, data["seller_product_id"], data.get("quantity", 1))

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)
        if result is None:
            return jsonify({"success": False, "message": "Failed to add item to cart"}), 400

        return jsonify({"success": True, "message": "Item added to cart", "data": result.to_dict()}), 201


@cart_bp.route('/items/<int:item_id>')
class CartItemDetail(MethodView):

    @cart_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Business logic validation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Cart item not found"},
        "422": {"description": "Input validation failed"},
    })
    @cart_bp.arguments(CartItemUpdateSchema, location="json")
    @roles_required(*_CART_ROLES)
    @cart_bp.response(200, CartItemSchema)
    def patch(self, data, item_id):
        """Set an absolute quantity for a cart line (stock-capped)."""
        jwt_user_id = get_jwt_identity()

        result = update_cart_item(jwt_user_id, item_id, data["quantity"])

        if isinstance(result, ValidationResponse):
            abort(result.status_code, message=result.message)
        if result is None:
            return jsonify({"success": False, "message": "Failed to update cart item"}), 400

        return jsonify({"success": True, "message": "Cart item updated", "data": result.to_dict()}), 200

    @cart_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Cart item not found"},
    })
    @roles_required(*_CART_ROLES)
    @cart_bp.response(200)
    def delete(self, item_id):
        """Remove a single line from the cart."""
        jwt_user_id = get_jwt_identity()
        result = remove_cart_item(jwt_user_id, item_id)
        return jsonify({"success": result.success, "message": result.message}), result.status_code
