from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def roles_required(*allowed_roles):
    """
    Decorator that checks if the current user has one of the allowed roles.

    Usage:
        @roles_required('ADMIN', 'SELLER')
        def my_route():
            ...

    How it works:
        1. Verifies the JWT is present and valid (like @jwt_required())
        2. Reads the 'roles' claim (array) from the JWT payload
        3. Returns 403 if none of the user's roles are in the allowed list
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_roles = claims.get("roles", [])

            if not any(r in allowed_roles for r in user_roles):
                return jsonify({
                    "error": "Forbidden",
                    "message": f"Access denied. Required role(s): {', '.join(allowed_roles)}"
                }), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
