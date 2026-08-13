from flask import Blueprint, jsonify,abort,request
from app.services import get_all_users,add_new_users,get_user_by,ValidationResponse
users_bp = Blueprint('users', __name__)

@users_bp.get('/')
def get_users():
    all_users = get_all_users()
    if not all_users:
        abort(500, description="Failed fetching data from database.")
    return jsonify({
        "success":True,
        "message": "Users retrieved successfully.",
        "data":[user.to_dict() for user in all_users]
    }), 200

@users_bp.get('/<int:id>')
def get_user_by_id(id):
    user_data = get_user_by(id)
    if not user_data:
        abort(404, description="User is not found")
    return jsonify({
        "success":True,
        "message": f"User with id={id} is found",
        "data":user_data.to_dict()
    }), 200

@users_bp.post('/')
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