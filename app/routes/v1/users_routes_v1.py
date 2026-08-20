from flask.views import MethodView
from flask import request, jsonify
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.services.auth_service import roles_required
from app.models import UserRole
from app.schemas import UserSchema, UserUpdateFormSchema, UserUpdateSuccessResponseSchema, UserErrorExamples, DeleteActionSchema
from app.permissions.field_filter import get_delete_policy
from app.services.user_service import (
    get_all_users,
    add_new_users,
    get_user_by,
    delete_user,
    update_user_by,
    become_seller,
    ValidationResponse
)

users_bp = Blueprint(
    'users',
    __name__,
    url_prefix='/api/v1/users',
    description='User Data Operations'
)


@users_bp.route('/')
class UsersRoot(MethodView):

    @users_bp.doc(security=[{"BearerAuth": []}])
    @users_bp.response(200, UserSchema(many=True))
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self):
        """Show all users where deleted_at is None"""
        all_users = get_all_users()
        if all_users is None:
            abort(500, message="Failed to retrieve data from database.")
        return jsonify({"success":True,"message":"show all users succssfull","data":all_users}),200

    @users_bp.doc(responses=UserErrorExamples.RESPONSES_POST_USER, security=[{"BearerAuth": []}])
    @users_bp.arguments(UserSchema, location="json")
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @users_bp.response(201, UserSchema)
    def post(self, user_instance):
        """Add a new user to the database"""
        result = add_new_users(user_instance)
        if isinstance(result, ValidationResponse):
            abort(400, messages=result.message)

        return result


@users_bp.route('/<int:id>')
class UserDetail(MethodView):

    @users_bp.response(200, UserSchema)
    def get(self, id):
        """Get user detail by ID"""
        user_data = get_user_by(id)
        if not user_data:
            abort(404, messages="User not found.")
        return user_data

    @users_bp.doc(responses=UserErrorExamples.RESPONSES_PUT_USER, security=[{"BearerAuth": []}])
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @users_bp.arguments(UserUpdateFormSchema, location="json")
    @users_bp.response(200, UserUpdateSuccessResponseSchema)
    def put(self, user_instance, id):
        """
        Update user profile.
        Requires JWT Bearer token. Admin/Superadmin can update any user.
        """
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        caller_roles = claims.get("roles", [])

        # Only admin/superadmin can modify other users
        is_admin = any(r in ("ADMIN", "SUPERADMIN") for r in caller_roles)
        if current_user_id != id and not is_admin:
            abort(403, message="You can only modify your own profile.")

        result = update_user_by(id, user_instance, caller_roles)
        if isinstance(result, ValidationResponse):
            if "OAuth" in result.message:
                abort(403, message=result.message)
            if "permission" in result.message.lower():
                abort(403, message=result.message)
            abort(400, message=result.message)
        form_data = {}

        if result.age is not None and result.age != "":
            if request.json and request.json.get('age'):
                form_data["age"] = ["age has updated"]

        if result.provider_key is not None and result.provider_key != "":
            if request.json and request.json.get('password'):
                form_data["password"] = ["password has updated"]

        if request.json and request.json.get('roles'):
            updated_roles = request.json.get('roles')
            form_data["roles"] = [f"roles for userid: {id} updated to roles: {updated_roles}"]

        if request.json and request.json.get('is_active') is not None:
            form_data["is_active"] = ["is_active has updated"]

        success_response = {"form": form_data}

        return success_response, 200


    @users_bp.doc(security=[{"BearerAuth": []}])
    @users_bp.arguments(DeleteActionSchema, location="json")
    @roles_required(UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @users_bp.response(200, UserSchema)
    def delete(self, delete_data, id):
        """Delete a user by ID. Default=soft delete. Superadmin can pass {"action":"hard"}."""
        claims = get_jwt()
        caller_roles = claims.get("roles", [])
        action = delete_data.get("action", "soft")

        result = delete_user(id, caller_roles, action)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        if result:
            return jsonify({"success": True, "message": result["message"]}), 200
        else:
            return jsonify({"success": False, "message": "Failed to delete user"}), 400


@users_bp.route('/become-seller')
class UserBecomeSeller(MethodView):

    @users_bp.doc(responses=UserErrorExamples.RESPONSES_BECOME_SELLER, security=[{"BearerAuth": []}])
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    @users_bp.response(200, UserSchema)
    def post(self):
        """
        Activate seller role for the current user.
        Adds SELLER to the user's role array. Requires JWT Bearer token.
        """
        current_user_id = int(get_jwt_identity())

        result = become_seller(current_user_id)
        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        return result
