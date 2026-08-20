import marshmallow as ma


# =============================================================================
# INPUT SCHEMAS - What the client sends to the server
# =============================================================================

class RegisterSchema(ma.Schema):
    """Schema for POST /auth/register (normal email+password signup)"""
    email = ma.fields.Email(
        required=True,
        error_messages={
            "required": "Email is not provided.",
            "invalid": "Email format is wrong."
        }
    )
    password = ma.fields.Str(
        required=True,
        validate=ma.validate.Length(min=6, error="Password must be at least 6 characters."),
        error_messages={"required": "Password is not provided."}
    )
    age = ma.fields.Int(
        required=True,
        validate=ma.validate.Range(min=18, error="You must be at least 18 years old."),
        error_messages={
            "required": "Age is not provided.",
            "invalid": "'age' must be a valid number."
        }
    )


class LoginSchema(ma.Schema):
    """Schema for POST /auth/login (normal email+password login)"""
    email = ma.fields.Email(
        required=True,
        error_messages={
            "required": "Email is not provided.",
            "invalid": "Email format is wrong."
        }
    )
    password = ma.fields.Str(
        required=True,
        error_messages={"required": "Password is not provided."}
    )


class OAuthGoogleSchema(ma.Schema):
    """Schema for POST /auth/oauth/google (Google OAuth login/register)"""
    id_token = ma.fields.Str(
        required=True,
        error_messages={"required": "Google ID token is not provided."}
    )
    age = ma.fields.Int(
        required=True,
        validate=ma.validate.Range(min=18, error="You must be at least 18 years old."),
        error_messages={
            "required": "Age is not provided.",
            "invalid": "'age' must be a valid number."
        }
    )


# =============================================================================
# RESPONSE SCHEMAS - What the server returns to the client
# =============================================================================

class TokenResponseSchema(ma.Schema):
    """Response schema for successful authentication"""
    access_token = ma.fields.Str(required=True, metadata={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."})
    user_id = ma.fields.Int(required=True, metadata={"example": 1})
    email = ma.fields.Str(required=True, metadata={"example": "rafaelalun@gmail.com"})
    username = ma.fields.Str(required=True, metadata={"example": "rafaelalun"})
    is_active = ma.fields.Bool(required=True, metadata={"example": False})
    message = ma.fields.Str(required=True, metadata={"example": "Registration successful. Please verify your email."})


class EmailConfirmationResponseSchema(ma.Schema):
    """Response schema for email confirmation"""
    message = ma.fields.Str(required=True, metadata={"example": "Email verified successfully."})
    is_active = ma.fields.Bool(required=True, metadata={"example": True})


# =============================================================================
# DATA HOLDER CLASS - Error Response Examples for Swagger Examples Dropdown
# =============================================================================

class AuthErrorExamples:
    """Reusable error response examples for auth routes."""

    # --- 422: JSON Validation Failed ---
    EMAIL_INVALID = {
        "summary": "Invalid Email Format",
        "value": {
            "code": 422,
            "errors": {"json": {"email": ["Email format is wrong."]}},
            "status": "Unprocessable Entity"
        }
    }

    PASSWORD_MISSING = {
        "summary": "Password Not Provided",
        "value": {
            "code": 422,
            "errors": {"json": {"password": ["Password is not provided."]}},
            "status": "Unprocessable Entity"
        }
    }

    PASSWORD_TOO_SHORT = {
        "summary": "Password Too Short",
        "value": {
            "code": 422,
            "errors": {"json": {"password": ["Password must be at least 6 characters."]}},
            "status": "Unprocessable Entity"
        }
    }

    AGE_MISSING = {
        "summary": "Age Not Provided",
        "value": {
            "code": 422,
            "errors": {"json": {"age": ["Age is not provided."]}},
            "status": "Unprocessable Entity"
        }
    }

    AGE_UNDERAGE = {
        "summary": "User Under 18",
        "value": {
            "code": 422,
            "errors": {"json": {"age": ["You must be at least 18 years old."]}},
            "status": "Unprocessable Entity"
        }
    }

    GOOGLE_TOKEN_MISSING = {
        "summary": "Google ID Token Not Provided",
        "value": {
            "code": 422,
            "errors": {"json": {"id_token": ["Google ID token is not provided."]}},
            "status": "Unprocessable Entity"
        }
    }

    # --- 400: Business Logic Failed ---
    EMAIL_ALREADY_REGISTERED = {
        "summary": "Email Already Registered",
        "value": {
            "code": 400,
            "errors": "Email 'rafaelalun@gmail.com' is already registered.",
            "status": "Bad Request"
        }
    }

    INVALID_CREDENTIALS = {
        "summary": "Invalid Email or Password",
        "value": {
            "code": 400,
            "errors": "Invalid email or password.",
            "status": "Bad Request"
        }
    }

    ACCOUNT_DEACTIVATED = {
        "summary": "Account Has Been Deactivated",
        "value": {
            "code": 400,
            "errors": "This account has been deactivated.",
            "status": "Bad Request"
        }
    }

    EMAIL_NOT_VERIFIED = {
        "summary": "Email Not Yet Verified",
        "value": {
            "code": 400,
            "errors": "Please verify your email before logging in.",
            "status": "Bad Request"
        }
    }

    GOOGLE_TOKEN_INVALID = {
        "summary": "Google ID Token Verification Failed",
        "value": {
            "code": 400,
            "errors": "Google ID token is invalid or expired.",
            "status": "Bad Request"
        }
    }

    CONFIRMATION_TOKEN_INVALID = {
        "summary": "Email Confirmation Token Invalid or Expired",
        "value": {
            "code": 400,
            "errors": "Confirmation token is invalid or has expired.",
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
