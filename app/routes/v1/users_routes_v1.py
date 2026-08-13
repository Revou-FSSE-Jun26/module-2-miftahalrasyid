from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.schemas import UserSchema
from app.services.user_service import get_all_users,add_new_users,get_user_by,ValidationResponse
# users_bp = Blueprint('users', __name__)

users_bp = Blueprint(
    'users', 
    __name__, 
    url_prefix='/api/v1/users', 
    description='Operasi Data Pengguna (Users)'
)

@users_bp.route('/')
class UsersRoot(MethodView):

    @users_bp.response(200, UserSchema(many=True))
    def get(self):
        """Mengambil semua daftar user dari database"""
        all_users = get_all_users()
        if all_users is None:
            abort(500, message="Gagal mengambil data dari database.")
        return all_users

    # location="form" memberi tahu Swagger untuk menyediakan input Multipart Form Data
    
    @users_bp.doc(responses={
        "422": {
            "description": "Kumpulan Variasi Gagal Validasi Input Form-Data",
            "content": {
                "application/json": {
                    "examples": {
                        # --- SKENARIO 1: Kasus Email Salah Format ---
                        "EmailInvalid": {
                            "summary": "Kasus Email Salah Format",
                            "value": {
                                "code": 422,
                                "errors": {
                                    "form": {
                                        "email": [
                                            "Email format is wrong."
                                        ]
                                    }
                                },
                                "status": "Unprocessable Entity"
                            }
                        },
                        # --- SKENARIO 2: Kasus Password Kosong ---
                        
                        "PasswordMissing": {
                            "summary": "Kasus Password Tidak Diinputkan",
                            "value": {
                                "code": 422,
                                "errors": {
                                    "form": {
                                        "email": [
                                            "Email is not provided."
                                        ],
                                        "age": [
                                            "Age is not provided."
                                        ],
                                        "password": [
                                            "Password is not provided."
                                        ]
                                    }
                                },
                                "status": "Unprocessable Entity"
                                
                            }
                        },
                        # --- SKENARIO 3: Kasus Umur Bukan Angka ---
                        "AgeInvalid": {
                            "summary": "Kasus Input Umur Bukan Angka",
                            "value": {
                                "code": 422,
                                "errors": {
                                    "form": {
                                        "age": [
                                            "'age' must be a valid number."
                                        ]
                                    }
                                },
                                "status": "Unprocessable Entity"
                            }
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Kumpulan Kasus Gagal Logika Bisnis",
            "content": {
                "application/json": {
                    "examples": {
                        # --- SKENARIO 1: Email Duplikat ---
                        "EmailDuplicated": {
                            "summary": "Kasus Email Sudah Terdaftar",
                            "value": {
                                "code": 400,
                                "errors": "Email 'rafaelalun@gmail.com' is already registered.",
                                "status": "Bad Request"
                            }
                        }
                        # Anda bisa menambahkan skenario 400 lainnya di bawah sini jika ada...
                    }
                }
            }
        }
    })
    @users_bp.arguments(UserSchema, location="form")
    @users_bp.response(201, UserSchema)
    def post(self, user_instance):
        """Mendaftarkan user baru ke dalam sistem"""
        # Di sini 'user_instance' sudah otomatis berupa objek Model User SQLAlchemy asli 
        # yang datanya sudah lengkap dan lolos validasi tipe data awal dari Marshmallow.
        result = add_new_users(user_instance)
        # Jika service layer mengembalikan kegagalan bisnis (misal email duplikat)
        if isinstance(result, ValidationResponse):
            abort(400, messages=result.message)
        
        # Jika sukses, kembalikan objek User. Smorest otomatis melakukan serialisasi JSON.
        return result

@users_bp.route('/<int:id>')
class UserDetail(MethodView):

    @users_bp.response(200, UserSchema)
    def get(self, id):
        """Mengambil data detail satu user berdasarkan ID"""
        user_data = get_user_by(id)
        if not user_data:
            abort(404, messages="User tidak ditemukan.")
        return user_data
