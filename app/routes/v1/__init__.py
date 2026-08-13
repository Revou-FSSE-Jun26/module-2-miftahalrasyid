from .auth_routes_v1 import auth_bp
from .product_routes_v1 import product_bp
from .users_routes_v1 import users_bp
from .orders_routes_v1 import order_bp
from app.routes import v1_bp

v1_bp.register_blueprint(auth_bp, url_prefix='/auth') 
v1_bp.register_blueprint(users_bp, url_prefix='/users') 
v1_bp.register_blueprint(product_bp, url_prefix='/products') 
v1_bp.register_blueprint(order_bp, url_prefix='/orders') 