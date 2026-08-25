from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models.address_model import Address
from app.extensions import db
from app.utils.sanitizer import SanitizeMixin


class AddressSchema(SanitizeMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = Address
        load_instance = True
        sqla_session = db.session
        include_fk = True

    # --- Input fields ---
    label          = ma.fields.Str(required=True, error_messages={"required": "Label is required (e.g. 'Home', 'Office')."})
    recipient_name = ma.fields.Str(required=True, error_messages={"required": "Recipient name is required."})
    phone          = ma.fields.Str(
        required=True,
        validate=ma.validate.Regexp(
            r'^\+62\d{8,13}$',
            error="Phone must be in international format starting with +62 (e.g. +6281234567890)."
        ),
        error_messages={"required": "Phone number is required."}
    )
    address_line   = ma.fields.Str(required=True, error_messages={"required": "Address line is required."})
    city           = ma.fields.Str(required=True, error_messages={"required": "City is required."})
    province       = ma.fields.Str(required=True, error_messages={"required": "Province is required."})
    postal_code    = ma.fields.Str(required=True, error_messages={"required": "Postal code is required."})
    is_default     = ma.fields.Bool(required=False, load_default=False)

    # --- dump_only ---
    id         = ma.fields.Int(dump_only=True)
    user_id    = ma.fields.Int(dump_only=True)
    created_at = ma.fields.DateTime(dump_only=True)


class AddressUpdateSchema(SanitizeMixin, ma.Schema):
    """Schema for updating an address (all fields optional)."""
    label          = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    recipient_name = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    phone          = ma.fields.Str(
        required=False,
        validate=ma.validate.Regexp(
            r'^\+62\d{8,13}$',
            error="Phone must be in international format starting with +62 (e.g. +6281234567890)."
        )
    )
    address_line   = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    city           = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    province       = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    postal_code    = ma.fields.Str(required=False, validate=ma.validate.Length(min=1))
    is_default     = ma.fields.Bool(required=False)
