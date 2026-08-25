from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models.profile_model import Profile
from app.extensions import db
from app.utils.sanitizer import SanitizeMixin


class ProfileSchema(SanitizeMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = Profile
        load_instance = True
        sqla_session = db.session
        include_fk = True

    # --- Input fields ---
    bio        = ma.fields.Str(required=False, allow_none=True, validate=ma.validate.Length(max=500))
    avatar_url = ma.fields.Str(required=False, allow_none=True, validate=ma.validate.Length(max=300))
    phone      = ma.fields.Str(
        required=False,
        allow_none=True,
        validate=ma.validate.Regexp(
            r'^\+62\d{8,13}$',
            error="Phone must be in international format starting with +62 (e.g. +6281234567890)."
        )
    )

    # --- dump_only ---
    id         = ma.fields.Int(dump_only=True)
    user_id    = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)
    updated_at = ma.fields.DateTime(dump_only=True)


class ProfileUpdateSchema(SanitizeMixin, ma.Schema):
    """Schema for updating a profile (all fields optional)."""
    bio        = ma.fields.Str(required=False, allow_none=True, validate=ma.validate.Length(max=500))
    avatar_url = ma.fields.Str(required=False, allow_none=True, validate=ma.validate.Length(max=300))
    phone      = ma.fields.Str(
        required=False,
        allow_none=True,
        validate=ma.validate.Regexp(
            r'^\+62\d{8,13}$',
            error="Phone must be in international format starting with +62 (e.g. +6281234567890)."
        )
    )
