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
    @users_bp.arguments(UserSchema, location="form")
    @users_bp.response(201, UserSchema)
    def post(self, user_instance):
        """Mendaftarkan user baru ke dalam sistem"""
        # Di sini 'user_instance' sudah otomatis berupa objek Model User SQLAlchemy asli 
        # yang datanya sudah lengkap dan lolos validasi tipe data awal dari Marshmallow.
        result = add_new_users(user_instance)

        # Jika service layer mengembalikan kegagalan bisnis (misal email duplikat)
        if isinstance(result, ValidationResponse):
            abort(400, message=result.message)
        
        # Jika sukses, kembalikan objek User. Smorest otomatis melakukan serialisasi JSON.
        return result

@users_bp.route('/<int:id>')
class UserDetail(MethodView):

    @users_bp.response(200, UserSchema)
    def get(self, id):
        """Mengambil data detail satu user berdasarkan ID"""
        user_data = get_user_by(id)
        if not user_data:
            abort(404, message="User tidak ditemukan.")
        return user_data
