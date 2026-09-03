from flask.views import MethodView
from flask import jsonify, request
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity

from app.schemas.payment_schema import (
    PaymentRequestSchema,
    PaymentResponseSchema,
    PaymentNotificationSchema,
    PaymentNotificationResponseSchema,
    PaymentErrorExamples,
)
from app.services.payment_service import initiate_payment, handle_notification
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
        "200": {"description": "Payment initiated. Order stays PENDING until Midtrans settlement webhook. Returns snap_token and redirect_url."},
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
        Initiate payment for a PENDING order via Midtrans Snap.
        Validates address/stock, creates a Snap transaction, and returns the
        snap_token + redirect_url. The order becomes PAID only after Midtrans
        confirms settlement through the /notification webhook.
        """
        jwt_user_id = get_jwt_identity()
        order_id = payment_data["order_id"]
        address_id = payment_data.get("address_id")

        result = initiate_payment(order_id, jwt_user_id, address_id)

        if isinstance(result, ValidationResponse):
            status_code = result.status_code or 400
            if status_code == 404:
                abort(404, message=result.message)
            elif status_code == 403:
                abort(403, message=result.message)
            else:
                abort(400, message=result.message)

        order = result["order"]
        order_dict = order.to_dict()
        order_dict["items"] = get_order_items(order.id)
        return jsonify({
            "success": True,
            "message": "Payment initiated. Complete payment via redirect_url.",
            "snap_token": result["snap_token"],
            "redirect_url": result["redirect_url"],
            "data": order_dict
        }), 200


@payment_bp.route('/notification')
class PaymentNotification(MethodView):

    @payment_bp.doc(responses={
        "200": {"description": "Notification processed (settlement -> order PAID, stock deducted; other statuses recorded)."},
        "400": {"description": "Missing order_id or settlement validation failed"},
        "403": {"description": "Invalid Midtrans signature"},
        "404": {"description": "No order matches the payment reference"},
    })
    @payment_bp.arguments(PaymentNotificationSchema, location="json")
    @payment_bp.response(200, PaymentNotificationResponseSchema)
    def post(self, notification):
        """
        Midtrans payment notification webhook (server-to-server, no JWT).
        Verifies the signature, then on settlement transitions the order
        PENDING -> PAID and deducts stock. Idempotent on repeated callbacks.
        """
        result = handle_notification(notification)

        # Always return 200 to Midtrans for handled-but-unsuccessful states so it
        # stops retrying, except for auth/lookup failures which use their code.
        status_code = result.status_code or 200
        if status_code in (403, 404):
            return jsonify({"success": False, "message": result.message}), status_code

        return jsonify({"success": result.success, "message": result.message}), 200
