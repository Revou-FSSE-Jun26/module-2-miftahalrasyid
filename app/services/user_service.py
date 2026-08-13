from app import db
from dataclasses import dataclass
from sqlalchemy.exc import IntegrityError
from app.models.user_model import User,UserRole
import logging
import hashlib
from email_validator import validate_email,EmailNotValidError

@dataclass
class ValidationResponse:
    success: bool
    message: str

def get_all_users():
    """
    Mengambil semua data pengguna dari database.
    Menerapkan error handling untuk mengantisipasi masalah koneksi database.
    """
    try:
        users = db.session.query(User).all()
        return users
    except Exception as e:
        logging.error(f"Gagal mengambil data users: {str(e)}")
        return None

def get_user_by(id):
    """
        Mengambil data pengguna melalui id.
        Menerapkan error handling untuk mengantisipasi masalah koneksi database.
    """
    try:
        user = db.session.query(User).get(id)
        return user
    except Exception as e:
        logging.error(f"Gagal mengambil data user ID {id}: {str(e)}")
        return None

def add_new_users(user_instance):
    """
    Menambah data pengguna baru ke database.
    Menerima 'user_instance' berupa objek Model User SQLAlchemy utuh dari Smorest.
    """
    # 1. Ambil data mentah dari properti objek yang dikirim oleh Smorest Gate
    email = user_instance.email
    password = user_instance.password

    # 2. Jalankan fungsi penormalan & validasi internet andalan Anda
    validated_email = normalize_and_validate_email(email)
    if validated_email is None:
        return ValidationResponse(success=False, message="Email format is wrong")
    
    try:
        # 3. Generate data otomatis internal sistem menggunakan kode asli Anda
        username = validated_email.split('@')[0]
        
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        user_instance.username = username
        user_instance.email = validated_email
        user_instance.provider_key = hashed_password      
        
        # Bersihkan properti password polos virtual agar tidak mengganggu SQLAlchemy
        if hasattr(user_instance, 'password'):
            delattr(user_instance, 'password')

        db.session.add(user_instance)
        db.session.commit()

        return user_instance 

    except IntegrityError as e:
        db.session.rollback()
        
        # Ambil pesan asli dari driver database Anda
        error_msg = str(e.orig)
        
        if "users_email_key" in error_msg or "already exists" in error_msg:
            return ValidationResponse(success=False, message=f"Email '{validated_email}' is already registered.")
        
        return ValidationResponse(success=False, message="Database integrity constraint violation.")

    except Exception as e:
        db.session.rollback()
        logging.error(f"Gagal memproses pendaftaran user: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected database error occurred.")

def normalize_and_validate_email(email_input):
    """
    Menormalisasi email untuk mencegah manipulasi alias (terutama Gmail).
    Contoh: 'andrew.twitter+youtube@gmail.com' -> 'andrew@gmail.com'
    """
    if not email_input or not isinstance(email_input, str):
        return None

    email_address = email_input.strip().lower()
    if '@' not in email_address:
        return None

    username_part, domain_part = email_address.split('@', 1)

    # Normalisasi khusus Gmail Anda yang sangat detail
    if domain_part in ['gmail.com', 'googlemail.com']:
        username_part = username_part.split('+')[0]  # Hapus bagian setelah +
        username_part = username_part.replace('.', '') # Hapus semua titik

    cleaned_email = f"{username_part}@{domain_part}"

    try:
        email_info = validate_email(cleaned_email, check_deliverability=True)
        return email_info.normalized
        
    except EmailNotValidError as e:
        logging.warning(f"Email tidak lolos validasi internet: {cleaned_email}. Alasan: {str(e)}")
        return None