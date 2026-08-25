import os
import logging
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Product, UserRole
from . import ValidationResponse

# Configuration
UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_IMAGES_PER_PRODUCT = 4


def _allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_extension(filename):
    """Get file extension."""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def upload_image(resource, resource_id, file, jwt_user_id, roles):
    """
    Upload an image file for a resource.
    
    Args:
        resource: Resource type string (e.g. "products")
        resource_id: ID of the resource
        file: FileStorage object from request.files
        jwt_user_id: Authenticated user's ID
        roles: User's roles from JWT
    
    Returns:
        dict with image path on success, ValidationResponse on error
    """
    from app.permissions import FIELD_PERMISSIONS

    # Check upload permission for this resource via RBAC
    can_upload = False
    bypass_ownership = False
    for role in roles:
        role_perms = FIELD_PERMISSIONS.get("uploads", {}).get(role, {})
        allowed_resources = role_perms.get("create", set())
        if resource in allowed_resources:
            can_upload = True
        if role_perms.get("bypass_ownership", False):
            bypass_ownership = True

    if not can_upload:
        return ValidationResponse(success=False, message=f"Your role does not have permission to upload files for '{resource}'")

    # Validate file presence
    if file is None or file.filename == '':
        return ValidationResponse(success=False, message="No file provided")

    # Validate file extension
    if not _allowed_file(file.filename):
        return ValidationResponse(success=False, message=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Validate file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_FILE_SIZE:
        return ValidationResponse(success=False, message=f"File size exceeds the maximum limit of {MAX_FILE_SIZE // (1024 * 1024)}MB")

    # Resource-specific logic
    if resource == "products":
        return _upload_product_image(resource_id, file, jwt_user_id, bypass_ownership)

    return ValidationResponse(success=False, message="Upload handler not implemented for this resource")


def _upload_product_image(product_id, file, jwt_user_id, bypass_ownership):
    """Handle image upload for a product."""
    try:
        product = Product.query.filter(
            Product.id == product_id,
            Product.deleted_at.is_(None)
        ).first()

        if not product:
            return ValidationResponse(success=False, message="Product not found")

        # Ownership check (superadmin bypasses)
        if not bypass_ownership:
            if product.user_id != int(jwt_user_id):
                return ValidationResponse(success=False, message="You can only upload images to your own products")

        # Check max images limit
        current_images = product.images or []
        if len(current_images) >= MAX_IMAGES_PER_PRODUCT:
            return ValidationResponse(success=False, message=f"Maximum {MAX_IMAGES_PER_PRODUCT} images per product reached")

        # Build file path: uploads/products/<uuid>/<slug>_<filename>.<ext>
        ext = _get_extension(file.filename)
        safe_original = secure_filename(file.filename.rsplit('.', 1)[0])
        final_filename = f"{product.slug}_{safe_original}.{ext}"

        folder_path = os.path.join(UPLOAD_ROOT, 'products', product.uuid)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, final_filename)

        # Check if file already exists
        if os.path.exists(file_path):
            return ValidationResponse(success=False, message="An image with this name already exists for this product")

        # Save file
        file.save(file_path)

        # Build relative path for DB storage
        relative_path = f"products/{product.uuid}/{final_filename}"

        # Append to images array
        if product.images is None:
            product.images = [relative_path]
        else:
            product.images = product.images + [relative_path]

        db.session.commit()
        logging.info(f"Image uploaded for product {product_id}: {relative_path}")

        return {
            "success": True,
            "message": "Image uploaded successfully",
            "image_path": relative_path,
            "total_images": len(product.images)
        }

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to upload image for product {product_id}: {str(e)}")
        return None


def delete_image(resource, resource_id, filename, jwt_user_id, roles):
    """
    Delete a specific image from a resource.
    
    Args:
        resource: Resource type string (e.g. "products")
        resource_id: ID of the resource
        filename: Filename to delete
        jwt_user_id: Authenticated user's ID
        roles: User's roles from JWT
    
    Returns:
        dict on success, ValidationResponse on error
    """
    from app.permissions import FIELD_PERMISSIONS

    # Check delete permission via RBAC
    can_delete = False
    bypass_ownership = False
    for role in roles:
        role_perms = FIELD_PERMISSIONS.get("uploads", {}).get(role, {})
        delete_policy = role_perms.get("delete")
        if delete_policy is not None:
            can_delete = True
        if role_perms.get("bypass_ownership", False):
            bypass_ownership = True

    if not can_delete:
        return ValidationResponse(success=False, message="Your role does not have permission to delete uploaded files")

    if resource == "products":
        return _delete_product_image(resource_id, filename, jwt_user_id, bypass_ownership)

    return ValidationResponse(success=False, message=f"Delete not supported for resource '{resource}'")


def _delete_product_image(product_id, filename, jwt_user_id, bypass_ownership):
    """Handle image deletion for a product."""
    try:
        product = Product.query.filter(
            Product.id == product_id,
            Product.deleted_at.is_(None)
        ).first()

        if not product:
            return ValidationResponse(success=False, message="Product not found")

        # Ownership check (admin/superadmin bypass)
        if not bypass_ownership:
            if product.user_id != int(jwt_user_id):
                return ValidationResponse(success=False, message="You can only delete images from your own products")

        # Find the image in the array
        relative_path = f"products/{product.uuid}/{filename}"
        current_images = product.images or []

        if relative_path not in current_images:
            return ValidationResponse(success=False, message="Image not found for this product")

        # Remove from filesystem
        file_path = os.path.join(UPLOAD_ROOT, relative_path)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove from DB array
        product.images = [img for img in current_images if img != relative_path]
        db.session.commit()

        logging.info(f"Image deleted for product {product_id}: {relative_path}")
        return {"success": True, "message": "Image deleted successfully"}

    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to delete image for product {product_id}: {str(e)}")
        return None
