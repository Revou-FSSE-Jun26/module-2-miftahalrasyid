from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import User
from app.extensions import db
from app.utils.sanitizer import SanitizeMixin


class UserSchema(SanitizeMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True       # Smorest auto-creates a Model object from input
        sqla_session = db.session
        include_fk = True          # Auto-detect Foreign Keys

    # --- dump_only: not required during POST input ---
    username = ma.fields.Str(dump_only=True)
    provider_key = ma.fields.Str(dump_only=True)
    # provider is server-controlled (set by register/OAuth flows), never client input.
    # Declaring it as a plain Str dump_only field also overrides the auto-generated
    # Enum field whose Length validator crashes on the AuthProvider enum member.
    provider = ma.fields.Str(dump_only=True)

    # --- Input Validation & Custom Error Messages ---
    email = ma.fields.Email(
        required=True,
        error_messages={
            "required": "Email is not provided.",
            "invalid": "Email format is wrong."
        }
    )

    age = ma.fields.Int(
        required=True,
        error_messages={
            "required": "Age is not provided.",
            "invalid": "'age' must be a valid number."
        }
    )

    password = ma.fields.Str(
        required=True,
        load_only=True,
        error_messages={
            "required": "Password is not provided."
        },
        validate=ma.validate.Length(min=1, error="Password cannot be an empty string.")
    )

    @ma.pre_load
    def strip_input_strings(self, data, **kwargs):
        """
        Strip whitespace from all string inputs before validation.
        """
        if isinstance(data, dict):
            # Drop server-controlled fields if a client sends them, so they are
            # ignored rather than raising "Unknown field" on a dump_only field.
            for server_field in ('provider', 'provider_key', 'username'):
                data.pop(server_field, None)
            for field in ('email', 'password'):
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
        return data


class UserCreateSchema(SanitizeMixin, SQLAlchemyAutoSchema):
    """
    Input-only schema for POST /users. Declaring the writable fields explicitly
    (and excluding the server-generated columns) keeps the Swagger request body
    clean — no id/provider/created_at/deleted_at in the example.
    """
    class Meta:
        model = User
        load_instance = True
        sqla_session = db.session
        include_fk = True
        # Server-generated / server-controlled columns must never be client input.
        exclude = ("id", "username", "provider", "provider_key", "created_at", "deleted_at")

    email = ma.fields.Email(
        required=True,
        error_messages={
            "required": "Email is not provided.",
            "invalid": "Email format is wrong."
        }
    )
    age = ma.fields.Int(
        required=True,
        error_messages={
            "required": "Age is not provided.",
            "invalid": "'age' must be a valid number."
        }
    )
    password = ma.fields.Str(
        required=True,
        load_only=True,
        error_messages={"required": "Password is not provided."},
        validate=ma.validate.Length(min=1, error="Password cannot be an empty string.")
    )
    roles = ma.fields.List(
        ma.fields.Str(validate=ma.validate.OneOf(["BUYER", "SELLER", "ADMIN", "SUPERADMIN"])),
        required=False,
        load_default=["BUYER"],
        metadata={"example": ["ADMIN"]}
    )
    is_active = ma.fields.Bool(
        required=False,
        load_default=False,
        metadata={"example": True}
    )

    @ma.pre_load
    def strip_input_strings(self, data, **kwargs):
        if isinstance(data, dict):
            for field in ('email', 'password'):
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
        return data


# =============================================================================
# DATA HOLDER CLASS - Error Response Examples for Swagger Examples Dropdown
# =============================================================================

class UserErrorExamples:
    """Reusable error response examples for user routes."""

    # --- 422: JSON Validation Failed ---
    EMAIL_INVALID = {
        "summary": "Invalid Email Format",
        "value": {
            "code": 422,
            "errors": {"json": {"email": ["Email format is wrong."]}},
            "status": "Unprocessable Entity"
        }
    }

    ALL_FIELDS_MISSING = {
        "summary": "All Required Fields Missing",
        "value": {
            "code": 422,
            "errors": {"json": {
                "email": ["Email is not provided."],
                "age": ["Age is not provided."],
                "password": ["Password is not provided."]
            }},
            "status": "Unprocessable Entity"
        }
    }

    AGE_INVALID = {
        "summary": "Age Is Not a Valid Number",
        "value": {
            "code": 422,
            "errors": {"json": {"age": ["'age' must be a valid number."]}},
            "status": "Unprocessable Entity"
        }
    }

    # --- 400: Business Logic Failed ---
    EMAIL_DUPLICATED = {
        "summary": "Email Already Registered",
        "value": {
            "code": 400,
            "errors": "Email 'rafaelalun@gmail.com' is already registered.",
            "status": "Bad Request"
        }
    }

    ALREADY_INACTIVE = {
        "summary": "Account Already Deactivated (Soft Delete)",
        "value": {
            "code": 400,
            "errors": "This user account is already deactivated.",
            "status": "Bad Request"
        }
    }

    ALREADY_SELLER = {
        "summary": "User Is Already a Seller",
        "value": {
            "code": 400,
            "errors": "You are already a seller.",
            "status": "Bad Request"
        }
    }

    # --- 401: Unauthorized (JWT) ---
    TOKEN_MISSING = {
        "summary": "Authorization Token Missing",
        "value": {
            "code": 401,
            "errors": "Missing authorization token.",
            "status": "Unauthorized"
        }
    }

    TOKEN_EXPIRED = {
        "summary": "Authorization Token Expired",
        "value": {
            "code": 401,
            "errors": "Token has expired.",
            "status": "Unauthorized"
        }
    }

    TOKEN_INVALID = {
        "summary": "Authorization Token Invalid",
        "value": {
            "code": 401,
            "errors": "Token is invalid.",
            "status": "Unauthorized"
        }
    }

    # --- 403: Forbidden ---
    OAUTH_USER_CANNOT_UPDATE = {
        "summary": "OAuth User Cannot Update Profile",
        "value": {
            "code": 403,
            "errors": "OAuth users cannot modify profile data directly.",
            "status": "Forbidden"
        }
    }

    # --- 404: User Not Found ---
    USER_NOT_FOUND = {
        "summary": "User Not Found",
        "value": {
            "code": 404,
            "errors": "User not found.",
            "status": "Not Found"
        }
    }

    # =========================================================================
    # PRE-BUILT RESPONSE DOC DICTS - Use directly in @bp.doc(responses=...)
    # =========================================================================

    RESPONSES_AUTH_REQUIRED = {
        "401": {
            "description": "Authentication Required",
            "content": {
                "application/json": {
                    "examples": {
                        "TokenMissing": TOKEN_MISSING,
                        "TokenExpired": TOKEN_EXPIRED,
                        "TokenInvalid": TOKEN_INVALID,
                    }
                }
            }
        }
    }

    RESPONSES_PUT_USER = {
        "401": {
            "description": "Authentication Required",
            "content": {
                "application/json": {
                    "examples": {
                        "TokenMissing": TOKEN_MISSING,
                        "TokenExpired": TOKEN_EXPIRED,
                        "TokenInvalid": TOKEN_INVALID,
                    }
                }
            }
        },
        "403": {
            "description": "Forbidden - OAuth Users Cannot Update",
            "content": {
                "application/json": {
                    "examples": {
                        "OAuthBlocked": OAUTH_USER_CANNOT_UPDATE,
                    }
                }
            }
        },
        "404": {
            "description": "User Not Found",
            "content": {"application/json": {"example": USER_NOT_FOUND["value"]}}
        },
        "400": {
            "description": "Business Logic Failures (PUT)",
            "content": {
                "application/json": {
                    "examples": {
                        "AlreadyInactive": ALREADY_INACTIVE,
                    }
                }
            }
        },
        "422": {
            "description": "Update Profile Validation Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "AgeInvalid": AGE_INVALID,
                    }
                }
            }
        }
    }
    RESPONSES_POST_USER = {
        "422": {
            "description": "JSON Input Validation Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "EmailInvalid": EMAIL_INVALID,
                        "AllFieldsMissing": ALL_FIELDS_MISSING,
                        "AgeInvalid": AGE_INVALID,
                    }
                }
            }
        },
        "400": {
            "description": "Business Logic Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "EmailDuplicated": EMAIL_DUPLICATED,
                    }
                }
            }
        }
    }

    RESPONSES_BECOME_SELLER = {
        "401": {
            "description": "Authentication Required",
            "content": {
                "application/json": {
                    "examples": {
                        "TokenMissing": TOKEN_MISSING,
                        "TokenExpired": TOKEN_EXPIRED,
                    }
                }
            }
        },
        "400": {
            "description": "Business Logic Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "AlreadySeller": ALREADY_SELLER,
                        "AccountDeactivated": ALREADY_INACTIVE,
                    }
                }
            }
        },
    }


# =============================================================================
# SUCCESS RESPONSE SCHEMA (200) - Update/Delete User
# =============================================================================

# Container for custom success text arrays
class UpdateFieldsContainerSchema(ma.Schema):
    # Using ma.missing so the field only appears when populated
    age = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["age has updated"]})
    password = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["password has updated"]})
    roles = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["roles has updated"]})
    is_active = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["is_active has updated"]})
    user = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["user has been deleted"]})


# Main outer wrapper class to be used in routes
class UserUpdateSuccessResponseSchema(ma.Schema):
    form = ma.fields.Nested(UpdateFieldsContainerSchema, required=True)


class BecomeSellerDataSchema(ma.Schema):
    """The `data` payload returned by POST /users/become-seller."""
    id = ma.fields.Int(metadata={"example": 8})
    roles = ma.fields.List(ma.fields.Str(), metadata={"example": ["BUYER", "SELLER"]})


class BecomeSellerResponseSchema(ma.Schema):
    """Response envelope for POST /users/become-seller."""
    success = ma.fields.Bool(metadata={"example": True})
    message = ma.fields.Str(metadata={"example": "You are a seller now"})
    # data = ma.fields.Nested(BecomeSellerDataSchema)


class UserUpdateFormSchema(UserSchema):
    # --- Block fields that are NEVER changeable via PUT ---
    id = ma.fields.Int(dump_only=True)
    email = ma.fields.Email(dump_only=True)
    deleted_at = ma.fields.DateTime(dump_only=True)
    provider = ma.fields.Str(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)

    # --- RBAC-controlled fields (permission layer decides who can write) ---
    roles = ma.fields.List(
        ma.fields.Str(validate=ma.validate.OneOf(["BUYER", "SELLER", "ADMIN", "SUPERADMIN"])),
        required=False,
        load_default=None,
        allow_none=True
    )
    is_active = ma.fields.Bool(
        required=False,
        load_default=None,
        allow_none=True
    )

    # --- Actual updatable input fields ---
    age = ma.fields.Int(
        required=False,
        error_messages={
            "invalid": "'age' must be a valid number."
        }
    )
    password = ma.fields.Str(
        required=False,
        allow_none=True,
        load_only=True,
        validate=ma.validate.Length(min=1, error="Password cannot be an empty string.")
    )

    @ma.pre_load
    def strip_input_strings(self, data, **kwargs):
        """
        Strip whitespace from all string inputs before validation.
        """
        if isinstance(data, dict):
            for field in ('password',):
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
        return data

    @ma.validates_schema
    def validate_at_least_one_field(self, data, **kwargs):
        """
        Ensure the client provides at least one updatable field.
        """
        age_val = data.get('age')
        password_val = data.get('password')
        roles_val = data.get('roles')
        is_active_val = data.get('is_active')

        if isinstance(password_val, str):
            password_val = password_val.strip()

        has_something = (
            (age_val is not None and age_val != "") or
            (password_val is not None and password_val != "") or
            (roles_val is not None) or
            (is_active_val is not None)
        )
        if not has_something:
            raise ma.ValidationError(
                "You must provide at least one parameter to update ('age', 'password', 'roles', or 'is_active').",
                field_name="json"
            )
