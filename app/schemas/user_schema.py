from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import marshmallow as ma
from app.models import User
from app import db

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True       # Smorest otomatis membuatkan objek Model dari input
        sqla_session = db.session   # Menggunakan session database Anda
        include_fk = True          # Otomatis mendeteksi Foreign Key jika

    # --- KUNCI PERBAIKAN: Set sebagai dump_only agar tidak ditagih saat POST ---
    username = ma.fields.Str(dump_only=True)
    provider_key = ma.fields.Str(dump_only=True)
        # --- KUSTOMISASI PESAN ERROR UNTUK FIELD WAJIB ---
    
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
        Interseptor: Sebelum divalidasi oleh Length, otomatis bersihkan spasi 
        kosong di ujung teks password agar input "   " terbaca sebagai "".
        """
        if isinstance(data, dict) and "password" in data and isinstance(data["password"], str):
            data["password"] = data["password"].strip()
        return data

# 1. Kontainer untuk menampung teks array sukses kustom Anda
class UpdateFieldsContainerSchema(ma.Schema):
    # Semua menggunakan ma.missing agar kolomnya hanya muncul jika ada isinya
    age = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["age has updated"]})
    password = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["password has updated"]})
    
    # 💡 TAMBAHKAN KOLOM USER UNTUK SOFT DELETE DI SINI
    user = ma.fields.List(ma.fields.Str(), load_default=ma.missing, dump_default=ma.missing, metadata={"example": ["user has been deleted"]})

# 2. Kelas Utama Pembungkus Terluar yang akan dipanggil di Rute
class UserUpdateSuccessResponseSchema(ma.Schema):
    form = ma.fields.Nested(UpdateFieldsContainerSchema, required=True)
class UserUpdateFormSchema(UserSchema):
    email = ma.fields.Email(dump_only=True)
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
    action = ma.fields.Str(
        required=False, 
        load_default="update",
        metadata={"example": "delete"} # Membantu memunculkan contoh isi di Swagger
    )
    @ma.pre_load
    def strip_input_strings(self, data, **kwargs):
        """
        Interseptor: Sebelum divalidasi oleh Length, otomatis bersihkan spasi 
        kosong di ujung teks password agar input "   " terbaca sebagai "".
        """
        if isinstance(data, dict) and "password" in data and isinstance(data["password"], str):
            data["password"] = data["password"].strip()
        return data
    
    @ma.validates_schema
    def validate_at_least_one_field(self, data, **kwargs):
        """
        Memastikan klien wajib mengisi minimal salah satu antara 'age' atau 'password'.
        Jika keduanya kosong, None, atau string kosong, langsung lempar ValidationError.
        """
        # Jangan validasi jika klien sengaja memicu aksi soft-delete
        if data.get('action') == 'delete':
            return

        age_val = data.get('age')
        password_val = data.get('password')

        # Bersihkan string password jika isinya hanya spasi kosong ("   ")
        if isinstance(password_val, str):
            password_val = password_val.strip()

        # Kondisi Cacat: Jika kedua data tersebut tidak diisi/kosong
        if (age_val is None or age_val == "") and (password_val is None or password_val == ""):
            raise ma.ValidationError(
                "You must provide at least one parameter to update ('age' or 'password').",
                field_name="form" # Menaruh pesan error di dalam kelompok form
            )
