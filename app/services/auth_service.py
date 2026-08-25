import os
import hashlib
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from functools import wraps

from flask import current_app, jsonify
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user_model import User, UserRole, AuthProvider
from app.services.user_service import normalize_and_validate_email, ValidationResponse


# =============================================================================
# ROLE-BASED ACCESS DECORATOR
# =============================================================================
# Moved to app/middleware/auth.py — re-exported here for backward compatibility
from app.middleware.auth import roles_required  # noqa: F401


# =============================================================================
# JWT TOKEN GENERATION
# =============================================================================

def generate_token(user):
    """Generate a JWT access token with user identity and claims."""
    user_dict = user.to_dict()
    additional_claims = {
        "email"    : user.email,
        "username" : user.username,
        "roles"    : user_dict['roles'],
        "provider" : user.provider.value,
        "is_active": user.is_active,
    }
    access_token = create_access_token(
        identity          = str(user.id),
        additional_claims = additional_claims
    )
    return access_token


# =============================================================================
# REGISTER (Normal email + password)
# =============================================================================

def register_user(email, password, age):
    """
    Register a new user with email + password.
    Returns a JWT token on success or ValidationResponse on failure.
    """
    # Normalize & validate email
    validated_email = normalize_and_validate_email(email)
    if validated_email is None:
        return ValidationResponse(success=False, message="Email format is wrong.")

    # Check if email already exists
    existing_user = User.query.filter_by(email=validated_email).first()
    if existing_user:
        return ValidationResponse(success=False, message=f"Email '{validated_email}' is already registered.")

    try:
        # Create user (password is automatically hashed via User.password setter)
        username = validated_email.split('@')[0]

        new_user = User(
            username  = username,
            email     = validated_email,
            age       = age,
            provider  = AuthProvider.PASSWORD_HASH,
            is_active = False,                        # Not active until email is verified
            roles      = [UserRole.BUYER],
        )
        
        # Set password via setter (automatically hashed with Werkzeug PBKDF2)
        new_user.password = password

        db.session.add(new_user)
        db.session.commit()

        # Auto-create empty profile
        from app.services.profile_service import create_profile
        create_profile(new_user.id)

        # Send verification email
        send_verification_email(new_user)

        # Generate JWT
        access_token = generate_token(new_user)

        return {
            "access_token": access_token,
            "user_id"     : new_user.id,
            "email"       : new_user.email,
            "username"    : new_user.username,
            "is_active"   : new_user.is_active,
            "message"     : "Registration successful. Please verify your email."
        }

    except IntegrityError:
        db.session.rollback()
        return ValidationResponse(success=False, message=f"Email '{validated_email}' is already registered.")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to register user: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred during registration.")


# =============================================================================
# LOGIN (Normal email + password)
# =============================================================================

def login_user(email, password):
    """
    Authenticate user with email + password.
    Returns JWT token on success or ValidationResponse on failure.
    """
    # Normalize email for lookup
    validated_email = normalize_and_validate_email(email)
    if validated_email is None:
        return ValidationResponse(success=False, message="Invalid email or password.")

    user = User.query.filter_by(email=validated_email).first()

    # User not found
    if user is None:
        return ValidationResponse(success=False, message="Invalid email or password.")

    # Account is soft-deleted
    if user.deleted_at is not None:
        return ValidationResponse(success=False, message="This account has been deactivated.")

    # Check if user registered via OAuth (can't login with password)
    if user.provider != AuthProvider.PASSWORD_HASH:
        return ValidationResponse(success=False, message="This account uses Google OAuth. Please login with Google.")

    # Verify password with SHA256 fallback for legacy hashes
    try:
        if not user.verify_password(password):
            return ValidationResponse(success=False, message="Invalid email or password.")
    except (ValueError, TypeError):
        # If verification fails, try SHA256 for backward compatibility
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if user.provider_key != password_hash:
            return ValidationResponse(success=False, message="Invalid email or password.")
        # Password verified with SHA256 - upgrade to Werkzeug PBKDF2
        user.password = password
        db.session.commit()
        logging.info(f"Upgraded password hash to PBKDF2 for user: {user.email}")

    # Check email verification
    if not user.is_active:
        return ValidationResponse(success=False, message="Please verify your email before logging in.")

    # Generate JWT
    access_token = generate_token(user)
    return {
        "access_token": access_token,
        "user_id"     : user.id,
        "email"       : user.email,
        "username"    : user.username,
        "is_active"   : user.is_active,
        "message"     : "Login successful."
    }


# =============================================================================
# OAUTH GOOGLE (Verify ID token + login or register)
# =============================================================================

def oauth_google_login(token, age):
    """
    Verify Google ID token, then login or register the user.
    Returns JWT token on success or ValidationResponse on failure.
    """
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID")

    try:
        # Verify the Google ID token
        idinfo = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            google_client_id
        )

        # Extract user info from verified token
        google_email = idinfo.get("email")
        google_sub = idinfo.get("sub")  # Unique Google user ID
        google_name = idinfo.get("name", "")

        if not google_email:
            return ValidationResponse(success=False, message="Google ID token does not contain an email.")

    except ValueError as e:
        logging.warning(f"Google token verification failed: {str(e)}")
        return ValidationResponse(success=False, message="Google ID token is invalid or expired.")

    # Check if user already exists
    user = User.query.filter_by(email=google_email).first()

    if user:
        # Existing user — check if soft-deleted
        if user.deleted_at is not None:
            return ValidationResponse(success=False, message="This account has been deactivated.")

        # Login existing OAuth user
        access_token = generate_token(user)
        return {
            "access_token": access_token,
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "message": "Login successful via Google."
        }

    # New user — register via OAuth
    try:
        username = google_email.split('@')[0]

        new_user = User(
            username=username,
            email=google_email,
            age=age,
            provider=AuthProvider.GOOGLE_OAUTH,
            provider_key=google_sub,  # Store Google sub ID as provider_key
            is_active=True,  # OAuth users are auto-verified (no email confirmation needed)
            roles=[UserRole.BUYER],
        )

        db.session.add(new_user)
        db.session.commit()

        # Auto-create empty profile
        from app.services.profile_service import create_profile
        create_profile(new_user.id)

        access_token = generate_token(new_user)

        return {
            "access_token": access_token,
            "user_id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
            "is_active": new_user.is_active,
            "message": "Registration via Google successful."
        }

    except IntegrityError:
        db.session.rollback()
        return ValidationResponse(success=False, message=f"Email '{google_email}' is already registered.")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to register OAuth user: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected error occurred during OAuth registration.")


# =============================================================================
# EMAIL CONFIRMATION
# =============================================================================

def confirm_email(token):
    """
    Verify the email confirmation token (JWT) and activate the user account.
    """
    from flask_jwt_extended import decode_token

    try:
        decoded = decode_token(token)
        user_id = decoded.get("sub")
        purpose = decoded.get("purpose")

        if purpose != "email_verification":
            return ValidationResponse(success=False, message="Confirmation token is invalid or has expired.")

        user = User.query.get(int(user_id))
        if user is None:
            return ValidationResponse(success=False, message="User not found.")

        if user.is_active:
            return {"message": "Email is already verified.", "is_active": True}

        user.is_active = True
        db.session.commit()

        return {"message": "Email verified successfully.", "is_active": True}

    except Exception as e:
        logging.warning(f"Email confirmation failed: {str(e)}")
        return ValidationResponse(success=False, message="Confirmation token is invalid or has expired.")


def generate_email_confirmation_token(user):
    """Generate a short-lived JWT token for email verification."""
    from datetime import timedelta
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"purpose": "email_verification"},
        expires_delta=timedelta(hours=24)
    )
    return token


# =============================================================================
# SMTP EMAIL SENDING
# =============================================================================

def send_verification_email(user):
    """
    Send an email verification link to the user's email address via Gmail SMTP.
    """
    email_user = os.environ.get("EMAIL_USER")
    email_pass = os.environ.get("EMAIL_PASS")
    base_url = os.environ.get("BASE_URL", "http://localhost:5000")

    if not email_user or not email_pass:
        logging.error("EMAIL_USER or EMAIL_PASS not configured in .env")
        return False

    # Generate confirmation token
    token = generate_email_confirmation_token(user)
    confirmation_url = f"{base_url}/api/v1/auth/email_confirmation?token={token}"

    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify Your Email - Rovodev Shop"
    msg["From"] = email_user
    msg["To"] = user.email

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Welcome to Rovodev Shop!</h2>
        <p>Hi <strong>{user.username}</strong>,</p>
        <p>Please click the button below to verify your email address:</p>
        <a href="{confirmation_url}" 
           style="display: inline-block; padding: 12px 24px; background-color: #4CAF50; 
                  color: white; text-decoration: none; border-radius: 4px; margin: 16px 0;">
            Verify Email
        </a>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #666;">{confirmation_url}</p>
        <p style="color: #999; font-size: 12px;">This link expires in 24 hours.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_user, email_pass)
            server.sendmail(email_user, user.email, msg.as_string())
        logging.info(f"Verification email sent to {user.email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send verification email: {str(e)}")
        return False
