from flask.views import MethodView
from flask import request
from flask_smorest import Blueprint, abort
from app.schemas import (
    RegisterSchema,
    LoginSchema,
    OAuthGoogleSchema,
    ResendVerificationSchema,
    TokenResponseSchema,
    EmailConfirmationResponseSchema,
    ResendVerificationResponseSchema,
    AuthErrorExamples,
)
from app.services.auth_service import (
    register_user,
    login_user,
    oauth_google_login,
    confirm_email,
    resend_verification_email,
)
from app.services.user_service import ValidationResponse

auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/api/v1/auth',
    description='Authentication & Authorization Operations'
)


@auth_bp.route('/register')
class AuthRegister(MethodView):

    @auth_bp.doc(responses={
        "422": {
            "description": "Registration Validation Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "EmailInvalid": AuthErrorExamples.EMAIL_INVALID,
                        "PasswordMissing": AuthErrorExamples.PASSWORD_MISSING,
                        "PasswordTooShort": AuthErrorExamples.PASSWORD_TOO_SHORT,
                        "AgeMissing": AuthErrorExamples.AGE_MISSING,
                        "AgeUnderage": AuthErrorExamples.AGE_UNDERAGE,
                    }
                }
            }
        },
        "400": {
            "description": "Business Logic Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "EmailAlreadyRegistered": AuthErrorExamples.EMAIL_ALREADY_REGISTERED,
                    }
                }
            }
        }
    })
    @auth_bp.arguments(RegisterSchema, location="json")
    @auth_bp.response(201, TokenResponseSchema)
    def post(self, data):
        """Register a new user with email and password. Sends a verification email."""
        result = register_user(
            email=data["email"],
            password=data["password"],
            age=data["age"]
        )

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        return result, 201


@auth_bp.route('/login')
class AuthLogin(MethodView):
    @auth_bp.arguments(
        LoginSchema,
        location="json",
        examples={
            "Super Admin Account": {
                "summary": "Log in as Super Admin",
                "value": {
                    "email": "funnyclown1112@gmail.com",
                    "password": "Password1234"
                }
            },
            "Regular Admin Account": {
                "summary": "Log in as Admin",
                "value": {
                    "email": "mike@gmail.com",
                    "password": "Password1234"
                }
            },
            "Seller Account": {
                "summary": "Log in as Seller",
                "value": {
                    "email": "justin@gmail.com",
                    "password": "Password1234"
                }
            },
            "Buyer Account": {
                "summary": "Log in as Buyer",
                "value": {
                    "email": "budi@gmail.com",
                    "password": "Password1234"
                }
            }
        }
    )
    @auth_bp.doc(responses={
        "422": {
            "description": "Login Validation Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "EmailInvalid": AuthErrorExamples.EMAIL_INVALID,
                        "PasswordMissing": AuthErrorExamples.PASSWORD_MISSING,
                    }
                }
            }
        },
        "400": {
            "description": "Business Logic Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "InvalidCredentials": AuthErrorExamples.INVALID_CREDENTIALS,
                        "AccountDeactivated": AuthErrorExamples.ACCOUNT_DEACTIVATED,
                        "EmailNotVerified": AuthErrorExamples.EMAIL_NOT_VERIFIED,
                    }
                }
            }
        }
    })
    # @auth_bp.arguments(LoginSchema, location="json")
    @auth_bp.response(200, TokenResponseSchema)
    def post(self, data):
        """Login with email and password. Returns a JWT access token."""
        result = login_user(
            email=data["email"],
            password=data["password"]
        )

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)
        return result


@auth_bp.route('/oauth/google')
class AuthOAuthGoogle(MethodView):

    @auth_bp.doc(responses={
        "422": {
            "description": "OAuth Validation Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "TokenMissing": AuthErrorExamples.GOOGLE_TOKEN_MISSING,
                        "AgeMissing": AuthErrorExamples.AGE_MISSING,
                        "AgeUnderage": AuthErrorExamples.AGE_UNDERAGE,
                    }
                }
            }
        },
        "400": {
            "description": "Business Logic Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "TokenInvalid": AuthErrorExamples.GOOGLE_TOKEN_INVALID,
                        "AccountDeactivated": AuthErrorExamples.ACCOUNT_DEACTIVATED,
                    }
                }
            }
        }
    })
    @auth_bp.arguments(OAuthGoogleSchema, location="json")
    @auth_bp.response(200, TokenResponseSchema)
    def post(self, data):
        """
        Login or register via Google OAuth.
        Frontend sends the Google ID token + age. Backend verifies the token.
        No email confirmation needed for OAuth users.
        """
        result = oauth_google_login(
            token=data["id_token"],
            age=data["age"]
        )

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        return result


@auth_bp.route('/resend_verification')
class AuthResendVerification(MethodView):

    @auth_bp.doc(responses={
        "422": {
            "description": "Validation Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "EmailInvalid": AuthErrorExamples.EMAIL_INVALID,
                    }
                }
            }
        },
        "502": {
            "description": "Email delivery failed",
        }
    })
    @auth_bp.arguments(ResendVerificationSchema, location="json")
    @auth_bp.response(200, ResendVerificationResponseSchema)
    def post(self, data):
        """Resend the verification email for a registered but unverified account."""
        result = resend_verification_email(email=data["email"])

        if isinstance(result, ValidationResponse):
            abort(result.status_code, message=result.message)

        return result


@auth_bp.route('/email_confirmation')
class AuthEmailConfirmation(MethodView):

    @auth_bp.doc(responses={
        "400": {
            "description": "Confirmation Failures",
            "content": {
                "application/json": {
                    "examples": {
                        "TokenInvalid": AuthErrorExamples.CONFIRMATION_TOKEN_INVALID,
                    }
                }
            }
        }
    })
    @auth_bp.response(200, EmailConfirmationResponseSchema)
    def get(self):
        """
        Verify email address via confirmation link.
        The token is passed as a query parameter: ?token=xxx
        """
        token = request.args.get("token")

        if not token:
            abort(400, message="Confirmation token is missing.")

        result = confirm_email(token)

        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)

        return result
