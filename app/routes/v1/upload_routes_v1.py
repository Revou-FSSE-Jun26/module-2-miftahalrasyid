from flask.views import MethodView
from flask import jsonify, request
from flask_smorest import Blueprint, abort
from app.models import UserRole
from app.services.auth_service import roles_required
from app.services.upload_service import upload_image, delete_image
from app.services import ValidationResponse
from flask_jwt_extended import get_jwt_identity, get_jwt

upload_bp = Blueprint(
    'uploads',
    __name__,
    url_prefix='/api/v1/uploads',
    description='File Upload Operations'
)


@upload_bp.route('/')
class UploadRoot(MethodView):

    @upload_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Business logic validation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "422": {"description": "Input validation failed"},
    })
    @upload_bp.response(201)
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def post(self):
        """
        Upload an image file for a resource.
        
        Multipart form data:
        - resource: string (e.g. "products")
        - resource_id: int (e.g. product ID)
        - file: image file (png, jpg, jpeg, webp | max 2MB)
        """
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()

        # Get form fields
        resource = request.form.get('resource')
        resource_id = request.form.get('resource_id')
        file = request.files.get('file')

        if not resource:
            abort(400, message="'resource' field is required (e.g. 'products')")
        if not resource_id:
            abort(400, message="'resource_id' field is required")

        try:
            resource_id = int(resource_id)
        except (ValueError, TypeError):
            abort(400, message="'resource_id' must be a valid integer")

        result = upload_image(resource, resource_id, file, jwt_user_id, roles)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        if result:
            return jsonify(result), 201
        else:
            return jsonify({"success": False, "message": "Failed to upload image"}), 400

    @upload_bp.doc(security=[{"BearerAuth": []}], responses={
        "400": {"description": "Delete operation failed"},
        "401": {"description": "Missing or invalid JWT token"},
        "403": {"description": "Insufficient permissions"},
        "404": {"description": "Resource not found"},
    })
    @upload_bp.response(200)
    @roles_required(UserRole.SELLER.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value)
    def delete(self):
        """
        Delete a specific image from a resource.
        
        JSON body:
        - resource: string (e.g. "products")
        - resource_id: int (e.g. product ID)
        - filename: string (exact filename to delete)
        """
        roles = get_jwt()['roles']
        jwt_user_id = get_jwt_identity()

        data = request.get_json(silent=True) or {}
        resource = data.get('resource')
        resource_id = data.get('resource_id')
        filename = data.get('filename')

        if not resource:
            abort(400, message="'resource' field is required")
        if not resource_id:
            abort(400, message="'resource_id' field is required")
        if not filename:
            abort(400, message="'filename' field is required")

        try:
            resource_id = int(resource_id)
        except (ValueError, TypeError):
            abort(400, message="'resource_id' must be a valid integer")

        result = delete_image(resource, resource_id, filename, jwt_user_id, roles)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        if result:
            return jsonify(result), 200
        else:
            return jsonify({"success": False, "message": "Failed to delete image"}), 400
