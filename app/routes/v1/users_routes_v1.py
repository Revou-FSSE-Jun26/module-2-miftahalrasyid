from flask.views import MethodView
from flask import request, jsonify
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.services.auth_service import roles_required
from app.models import UserRole
from app.schemas import UserSchema, UserUpdateFormSchema, UserUpdateSuccessResponseSchema, UserErrorExamples, DeleteActionSchema, ProfileUpdateSchema
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
from app.services.profile_service import get_profile_by_user_id, update_profile

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
        """Show all users. Supports ?page=1&per_page=10 (max 30)."""
        result = get_all_users()
        if result is None:
            abort(500, message="Failed to retrieve data from database.")
        return jsonify({
            "success": True,
            "message": "show all users successful",
            "data": [user.to_dict() for user in result["items"]],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total": result["count"],
            }
        }), 200

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
        """Get public user profile by ID (username only)."""
        user_data = get_user_by(id)
        if not user_data:
            abort(404, message="User not found.")
        # Public fields only
        return jsonify({
            "success": True,
            "message": "User profile",
            "data": {"id": user_data.id, "username": user_data.username}
        }), 200

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

        if not result.success:
            return jsonify({"success": False, "message": result.message}), result.status_code

        return jsonify({"success": True, "message": result.message}), result.status_code


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


@users_bp.route('/me')
class UserMe(MethodView):

    @users_bp.doc(security=[{"BearerAuth": []}])
    @users_bp.response(200)
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self):
        """Get the authenticated user's full profile (user data + profile)."""
        current_user_id = int(get_jwt_identity())
        user = get_user_by(current_user_id)
        if not user:
            abort(404, message="User not found.")

        profile = get_profile_by_user_id(current_user_id)

        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "age": user.age,
            "roles": [r.value for r in user.roles] if user.roles else [],
            "is_active": user.is_active,
            "provider": user.provider.value if user.provider else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "profile": profile.to_dict() if profile else None,
        }

        return jsonify({"success": True, "message": "Your profile", "data": data}), 200


@users_bp.route('/me/profile')
class UserMeProfile(MethodView):

    @users_bp.doc(security=[{"BearerAuth": []}])
    @users_bp.arguments(ProfileUpdateSchema, location="json")
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def put(self, update_data):
        """Update the authenticated user's profile (bio, avatar_url, phone)."""
        current_user_id = int(get_jwt_identity())

        result = update_profile(current_user_id, update_data)
        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        return jsonify({"success": True, "message": "Profile updated", "data": result.to_dict()}), 200


@users_bp.route('/me/addresses')
class UserMeAddresses(MethodView):

    @users_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
    })
    @users_bp.response(200)
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self):
        """Get all addresses for the authenticated user."""
        from app.services.address_service import get_addresses_by_user

        current_user_id = int(get_jwt_identity())
        addresses = get_addresses_by_user(current_user_id)

        if addresses is None:
            return jsonify({"success": False, "message": "Failed to retrieve addresses"}), 400

        return jsonify({
            "success": True,
            "message": "Your addresses",
            "data": [addr.to_dict() for addr in addresses]
        }), 200

    @users_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Maximum addresses reached or validation error"},
        "401": {"description": "Missing or invalid JWT token"},
        "422": {"description": "Input validation failed"},
    })
    @users_bp.response(201)
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def post(self):
        """Create a new address for the authenticated user."""
        from app.schemas import AddressSchema
        from app.services.address_service import create_address
        from marshmallow import ValidationError

        current_user_id = int(get_jwt_identity())
        schema = AddressSchema()

        try:
            address_instance = schema.load(request.json)
        except ValidationError as err:
            abort(422, message=err.messages)

        result = create_address(current_user_id, address_instance)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        return jsonify({"success": True, "message": "Address created", "data": result.to_dict()}), 201


@users_bp.route('/me/addresses/<int:address_id>')
class UserMeAddressDetail(MethodView):

    @users_bp.doc(security=[{"BearerAuth": []}], responses={
        "401": {"description": "Missing or invalid JWT token"},
        "404": {"description": "Address not found or does not belong to you"},
    })
    @users_bp.response(200)
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def get(self, address_id):
        """Get a specific address by ID for the authenticated user."""
        from app.services.address_service import get_address_by_id

        current_user_id = int(get_jwt_identity())
        address = get_address_by_id(address_id, current_user_id)

        if not address:
            abort(404, message="Address not found")

        return jsonify({"success": True, "data": address.to_dict()}), 200

    @users_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Update failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "404": {"description": "Address not found or does not belong to you"},
        "422": {"description": "Input validation failed"},
    })
    @users_bp.response(200)
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def put(self, address_id):
        """Update a specific address for the authenticated user."""
        from app.schemas import AddressUpdateSchema
        from app.services.address_service import update_address
        from marshmallow import ValidationError

        current_user_id = int(get_jwt_identity())
        schema = AddressUpdateSchema()

        try:
            update_data = schema.load(request.json)
        except ValidationError as err:
            abort(422, message=err.messages)

        result = update_address(address_id, current_user_id, update_data)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        return jsonify({"success": True, "message": "Address updated", "data": result.to_dict()}), 200

    @users_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Delete failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "404": {"description": "Address not found or does not belong to you"},
    })
    @users_bp.response(200)
    @roles_required(UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def delete(self, address_id):
        """Delete a specific address for the authenticated user."""
        from app.services.address_service import delete_address

        current_user_id = int(get_jwt_identity())
        result = delete_address(address_id, current_user_id)

        if not result.success:
            return jsonify({"success": False, "message": result.message}), 400

        return jsonify({"success": True, "message": result.message}), 200
