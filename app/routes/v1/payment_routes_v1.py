from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity, get_jwt

from app.schemas.payment_schema import PaymentRequestSchema, PaymentResponseSchema, PaymentErrorExamples
from app.services.payment_service import process_payment
from app.services import ValidationResponse
from app.models import UserRole
from app.services.auth_service import roles_required
from app.services.order_service import get_order_items

payment_bp = Blueprint(
    'payment',
    __name__,
    url_prefix='/api/v1/payment',
    description='Payment Processing Operations'
)


@payment_bp.route('/')
class PaymentRoot(MethodView):

    @payment_bp.doc(security=[{"BearerAuth": []}], responses={
        "200": {"description": "Payment processed successfully. Order status transitions to PAID, stock deducted, address set."},
        "400": {"description": "Business logic validation failed",
                "content": {"application/json": {"examples": {
                    "no_default_address": PaymentErrorExamples.NO_DEFAULT_ADDRESS,
                    "insufficient_stock": PaymentErrorExamples.INSUFFICIENT_STOCK,
                    "order_not_pending": PaymentErrorExamples.ORDER_NOT_PENDING,
                    "product_unavailable": PaymentErrorExamples.PRODUCT_UNAVAILABLE,
                }}}},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions or unauthorized to pay for this order",
                "content": {"application/json": {"examples": {
                    "unauthorized": PaymentErrorExamples.UNAUTHORIZED,
                }}}},
        "404": {"description": "Order or address not found",
                "content": {"application/json": {"examples": {
                    "order_not_found": PaymentErrorExamples.ORDER_NOT_FOUND,
                    "address_not_found": PaymentErrorExamples.ADDRESS_NOT_FOUND,
                }}}},
        "422": {"description": "Input validation failed",
                "content": {"application/json": {"examples": {
                    "order_id_missing": PaymentErrorExamples.ORDER_ID_MISSING,
                }}}},
    })
    @payment_bp.arguments(PaymentRequestSchema, location="json")
    @roles_required(UserRole.BUYER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @payment_bp.response(200, PaymentResponseSchema)
    def post(self, payment_data):
        """
        Process payment for a PENDING order.
        Validates address (explicit or default), deducts stock, transitions to PAID.
        """
        jwt_user_id = get_jwt_identity()
        order_id = payment_data["order_id"]
        address_id = payment_data.get("address_id")

        result = process_payment(order_id, jwt_user_id, address_id)

        if isinstance(result, ValidationResponse):
            status_code = result.status_code or 400
            if status_code == 404:
                abort(404, message=result.message)
            elif status_code == 403:
                abort(403, message=result.message)
            else:
                abort(400, message=result.message)

        if result:
            order_dict = result.to_dict()
            order_dict["items"] = get_order_items(result.id)
            return jsonify({
                "success": True,
                "message": "Payment processed successfully",
                "data": order_dict
            }), 200
        else:
            return jsonify({"success": False, "message": "Failed to process payment"}), 400
