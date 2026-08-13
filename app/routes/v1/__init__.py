from .auth_routes_v1 import auth_bp
from .product_routes_v1 import product_bp
from .users_routes_v1 import users_bp
from .orders_routes_v1 import order_bp

__all__ = ["auth_bp","product_bp","users_bp","order_bp"]