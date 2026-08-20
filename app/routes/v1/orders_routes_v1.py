from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.schemas import OrderSchema

order_bp = Blueprint(
    'orders',
    __name__,
    url_prefix='/api/v1/orders',
    description='Order Data Operations'
)


@order_bp.route('/')
class OrdersRoot(MethodView):

    def get(self):
        """Check active status of the Orders endpoint (Mock Data)"""
        return jsonify({"message": "Orders endpoint active"})
