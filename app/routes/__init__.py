from flask import Blueprint
# from .v2 import v1_bp

v1_bp = Blueprint('v1', __name__, url_prefix='/v1')

from .v1 import auth_bp,users_bp,product_bp,order_bp,category_bp

__all__ = ["auth_bp","users_bp","product_bp","order_bp","category_bp","v1_bp"]
