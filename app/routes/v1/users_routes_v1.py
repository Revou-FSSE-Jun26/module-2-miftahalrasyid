from flask.views import MethodView
from flask import request
from flask_smorest import Blueprint, abort
from app.schemas import UserSchema,UserUpdateFormSchema,UserUpdateSuccessResponseSchema
from app.services.user_service import (
    get_all_users,
    add_new_users,
    get_user_by,
    delete_user_by,
    update_user_by,
    ValidationResponse
)
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
        """Show all user list with deleted_at=None"""
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
        """add new user to the database"""
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
        """Get user detail by ID"""
        user_data = get_user_by(id)
        if not user_data:
            abort(404, messages="User tidak ditemukan.")
        return user_data
    @users_bp.doc(responses={
        "404": {
            "description": "User Tidak Ditemukan",
            "content": {"application/json": {"example": {"code": 404, "errors": "User tidak ditemukan.", "status": "Not Found"}}}
        },
        "400": {
            "description": "Kumpulan Kasus Gagal Logika Bisnis (PUT)",
            "content": {
                "application/json": {
                    "examples": {
                        "AlreadyInactive": {
                            "summary": "Kasus Soft Delete - Akun Sudah Nonaktif",
                            "value": {
                                "code": 400,
                                "errors": "Akun user ini memang sudah dinonaktifkan.",
                                "status": "Bad Request"
                            }
                        },
                        "EmailDuplicated": {
                            "summary": "Kasus Update - Email Baru Sudah Terdaftar",
                            "value": {
                                "code": 400,
                                "errors": "Email 'rafaelalun@gmail.com' is already registered.",
                                "status": "Bad Request"
                            }
                        }
                    }
                }
            }
        },
        "422": {
            "description": "Kumpulan Variasi Gagal Validasi Input Update Profil",
            "content": {
                "application/json": {
                    "examples": {
                        "EmailInvalid": {
                            "summary": "Kasus Format Email Salah",
                            "value": {"code": 422, "errors": {"form": {"email": ["Email format is wrong."]}}, "status": "Unprocessable Entity"}
                        },
                        "AgeInvalid": {
                            "summary": "Kasus Input Umur Bukan Angka",
                            "value": {"code": 422, "errors": {"form": {"age": ["'age' must be a valid number."]}}, "status": "Unprocessable Entity"}
                        }
                    }
                }
            }
        }
    })
    # Menggunakan UserUpdateFormSchema agar kolom text 'action' otomatis muncul di Form Postman / Swagger
    @users_bp.arguments(UserUpdateFormSchema, location="form") 
    @users_bp.response(200, UserUpdateSuccessResponseSchema)
    def put(self, user_instance, id):
        """
        Memperbarui Profil User / Melakukan Soft Delete via Form-Data.
        Ketik value 'delete' pada key 'action' di Form-Data untuk menonaktifkan akun.
        """
        # 1. Ambil nilai action yang dikirim dari teks form-data
        action_type = request.form.get('action', 'update').lower()

        # 2. Logika hapus tidak perlu delattr karena action_type dibaca terpisah
        if action_type == 'delete':
            result = delete_user_by(id)
            if isinstance(result, ValidationResponse):
                abort(400, message=result.message)
            success_response = {
                "form": {
                    "user": ["user has been deleted"]
                }
            }
            return success_response, 200
        
        result = update_user_by(id, user_instance)
        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)
        form_data = {}

        if result.age is not None and result.age != "":
            if request.form.get('age'):
                form_data["age"] = ["age has updated"]

        if result.provider_key is not None and result.provider_key != "":
            if request.form.get('password'):
                form_data["password"] = ["password has updated"]

        success_response = {"form": form_data}

        return success_response, 200 # Tetap 200 OK
