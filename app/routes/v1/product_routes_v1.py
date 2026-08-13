from flask import Blueprint, jsonify,abort,request
product_bp = Blueprint('products', __name__)


products = [
    {"id": 1, "name": "Laptop", "price": 15000000},
    {"id": 2, "name": "Mouse", "price": 250000},
    {"id": 3, "name": "Keyboard", "price": 500000},
    {"id": 4, "name": "Monitor", "price": 3500000}
]

@product_bp.get('/')
def get_products():
    return jsonify(products)

@product_bp.get('/<int:id>')
def get_product_by(id):

    has_product = next((product for product in products if product["id"] == id),None)
    if not has_product:
        return abort(404, description="Product is not found")
    return jsonify(has_product),200