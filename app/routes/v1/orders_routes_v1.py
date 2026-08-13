from flask import Blueprint, jsonify,abort,request
order_bp = Blueprint('orders', __name__)


@order_bp.get('/')
def get_orders():
    return jsonify({"message": "Orders endpoint active"})

