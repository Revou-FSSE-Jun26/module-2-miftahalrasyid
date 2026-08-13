from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.schemas import OrderSchema
# order_bp = Blueprint('orders', __name__)
order_bp = Blueprint(
    'orders', 
    __name__, 
    url_prefix='/api/v1/orders', 
    description='Operasi Data Pesanan (Orders - Mock Data)'
)

# 2. Bungkus ke dalam kelas MethodView agar dikenali oleh Smorest Engine
@order_bp.route('/')
class OrdersRoot(MethodView):

    def get(self):
        """Mengecek status aktif dari endpoint Orders (Mock Data)"""
        return jsonify({"message": "Orders endpoint active"})

