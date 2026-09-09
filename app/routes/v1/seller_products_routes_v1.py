from flask.views import MethodView
from flask import jsonify, request
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request

from app.models import UserRole
from app.services.auth_service import roles_required
from app.services import ValidationResponse
from app.services.seller_product_service import (
    browse_listings,
    get_my_listings,
    get_listing_by_id,
    create_listing,
    update_listing,
    delete_listing,
)
from app.schemas import (
    SellerProductCreateSchema,
    SellerProductUpdateSchema,
    SellerProductSchema,
    SellerProductBrowseSchema,
    SellerProductQueryArgs,
    DeleteActionSchema,
)


def _optional_identity():
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id is None:
            return None, []
        claims = get_jwt() or {}
        return user_id, claims.get("roles", [])
    except Exception:
        return None, []


seller_products_bp = Blueprint(
    'seller_products',
    __name__,
    url_prefix='/api/v1/seller-products',
    description='Seller product listings (per-seller offers)'
)


@seller_products_bp.route('/')
class SellerProductsRoot(MethodView):

    @seller_products_bp.arguments(SellerProductQueryArgs, location="query")
    @seller_products_bp.response(200, SellerProductBrowseSchema(many=True))
    def get(self, query_args):
        """
        Public storefront browse. Returns every ACTIVE, in-stock listing (joined
        to its catalog spec), each row tagged with the product's `min_price`.
        """
        _, roles = _optional_identity()
        result = browse_listings(query_args, roles=roles)
        if result is None:
            return jsonify({"success": False, "message": "Failed to retrieve listings"}), 400
        return jsonify({
            "success": True,
            "message": "get all listings successful",
            "data": result["items"],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            }
        }), 200

    @seller_products_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Business logic validation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "422": {"description": "Input validation failed"},
    })
    @seller_products_bp.arguments(SellerProductCreateSchema, location="json")
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @seller_products_bp.response(201, SellerProductSchema)
    def post(self, data):
        """Create a listing (Option B: find-or-create catalog + PENDING listing)."""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()

        listing = create_listing(data, jwt_user_id, roles)
        if isinstance(listing, ValidationResponse):
            abort(400, message=listing.message)
        if listing:
            return jsonify({"success": True, "message": "Listing created successfully", "data": listing.to_dict()}), 201
        return jsonify({"success": False, "message": "Failed to create listing"}), 400


@seller_products_bp.route('/mine')
class SellerProductsMine(MethodView):

    @seller_products_bp.doc(security=[{"BearerAuth": []}])
    @seller_products_bp.arguments(SellerProductQueryArgs, location="query")
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @seller_products_bp.response(200, SellerProductSchema(many=True))
    def get(self, query_args):
        """List the caller's own listings (any status). Admin sees all."""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()
        result = get_my_listings(query_args, jwt_user_id=jwt_user_id, roles=roles)
        if result is None:
            return jsonify({"success": False, "message": "Failed to retrieve listings"}), 400

        from app.permissions.field_filter import get_allowed_fields
        allowed = get_allowed_fields("seller_products", roles, "read") or None
        return jsonify({
            "success": True,
            "message": "get my listings successful",
            "data": [sp.to_dict(allowed_fields=allowed) for sp in result["items"]],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            }
        }), 200


@seller_products_bp.route('/<int:id>')
class SellerProductDetail(MethodView):

    @seller_products_bp.response(200, SellerProductSchema)
    def get(self, id):
        """Retrieve a single listing by ID (visibility-aware)."""
        jwt_user_id, roles = _optional_identity()
        listing = get_listing_by_id(id, jwt_user_id=jwt_user_id, roles=roles)
        if not listing:
            abort(404, message="Listing is not found")

        data = listing.to_dict()
        if listing.catalog:
            data.update({
                "brand": listing.catalog.brand,
                "name": listing.catalog.name,
                "model": listing.catalog.model,
                "color": listing.catalog.color,
                "size": listing.catalog.size,
            })
        return jsonify({"success": True, "message": "get listing detail successful", "data": data}), 200

    @seller_products_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Business logic validation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
        "422": {"description": "Input validation failed"},
    })
    @seller_products_bp.arguments(SellerProductUpdateSchema, location="json")
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @seller_products_bp.response(200, SellerProductSchema)
    def put(self, update_data, id):
        """Update a listing. Seller: title/price/stock/sku + ACTIVE<->INACTIVE. Admin: approve/suspend/reject."""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()
        listing = update_listing(id, update_data, jwt_user_id, roles)
        if isinstance(listing, ValidationResponse):
            abort(400, message=listing.message)
        if listing:
            return jsonify({"success": True, "message": "Listing updated successfully", "data": listing.to_dict()}), 200
        return jsonify({"success": False, "message": "Failed to update listing"}), 400

    @seller_products_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Delete operation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
    })
    @seller_products_bp.arguments(DeleteActionSchema, location="json")
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @seller_products_bp.response(200)
    def delete(self, delete_data, id):
        """Delete a listing. Default=soft. Superadmin can pass {"action":"hard"}."""
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()
        action = delete_data.get("action", "soft")
        result = delete_listing(id, jwt_user_id, roles, action)
        if not result.success:
            return jsonify({"success": False, "message": result.message}), result.status_code
        return jsonify({"success": True, "message": result.message}), result.status_code
