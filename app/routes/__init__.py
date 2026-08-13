from flask import Blueprint
# from .v2 import v1_bp
from .v1 import auth_bp,users_bp,product_bp,order_bp

v1_bp = Blueprint('v1', __name__, url_prefix='/api/v1')

v1_bp.register_blueprint(auth_bp, url_prefix='/auth') 
v1_bp.register_blueprint(users_bp, url_prefix='/users') 
v1_bp.register_blueprint(product_bp, url_prefix='/products') 
v1_bp.register_blueprint(order_bp, url_prefix='/orders') 