from flask import Blueprint, jsonify, abort, request
from app.services import get_all_users,add_new_users,get_user_by,ValidationResponse

v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

products = [
    {"id": 1, "name": "Laptop", "price": 15000000},
    {"id": 2, "name": "Mouse", "price": 250000},
    {"id": 3, "name": "Keyboard", "price": 500000},
    {"id": 4, "name": "Monitor", "price": 3500000}
]

@v1_bp.get('/users')
def get_users():
    all_users = get_all_users()
    if not all_users:
        abort(500, description="Failed fetching data from database.")
    return jsonify({
        "success":True,
        "message": "Users retrieved successfully.",
        "data":[user.to_dict() for user in all_users]
    }), 200

@v1_bp.get('/user/<int:id>')
def get_user_by_id(id):
    user_data = get_user_by(id)
    if not user_data:
        abort(404, description="User is not found")
    return jsonify({
        "success":True,
        "message": f"User with id={id} is found",
        "data":user_data.to_dict()
    }), 200

@v1_bp.post('/users')
def register_new_users():
    email,age,password = (request.form.get('email'),request.form.get('age'),request.form.get('password') )

    result = add_new_users(email=email, age=age, password=password)

    if isinstance(result, ValidationResponse):
        return jsonify({
            "success": result.success,
            "message": result.message
        }), 400
    
    return jsonify({
        "success": True,
        "message": " New user has been created.",
        "data": result.to_dict()
    }), 201





@v1_bp.get('/orders')
def get_orders():
    return jsonify({"message": "Orders endpoint active"})

@v1_bp.get('/products')
def get_products():
    return jsonify(products)

@v1_bp.get('/products/<int:id>')
def get_product_by(id):

    has_product = next((product for product in products if product["id"] == id),None)
    if not has_product:
        return abort(404, description="Product is not found")
    return jsonify(has_product),200