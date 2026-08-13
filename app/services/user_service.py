from app import db
from dataclasses import dataclass
from sqlalchemy.exc import IntegrityError
from app.models.user_model import User
import logging
import hashlib

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

def add_new_users(email,age,password):
    """
    Menambah data pengguna baru ke database.
    Menerapkan error handling untuk mengantisipasi masalah koneksi database.
    """
    
    required_arguments = (email,age,password)
    has_required_arguments = all(arg is not None for arg in required_arguments)
    if not has_required_arguments:
        return ValidationResponse(success=False, message="'email','age',or 'password' is not provided")

    if '@' not in email:
        return ValidationResponse(success=False, message="Email format is wrong")

    validated_email = normalize_and_validate_email(email)

    try: 
        validate_age = int(age)
    except Exception as e:
        return ValidationResponse(success=False, message="'age' must be a valid number")
    
    try:
        username = validated_email.split('@')[0]

        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        is_active = False  # Akun baru dibuat dengan status tidak aktif terlebih dahulu

        new_user = User(
            username=username,
            email=validated_email,
            age=validate_age,
            is_active=is_active,
            provider_key=hashed_password # Hash SHA-256 disimpan ke kolom provider_key
        )

        db.session.add(new_user)
        db.session.commit()

        return new_user

    except IntegrityError as e:
        db.session.rollback()
        
        # Ambil pesan asli dari driver psycopg2
        error_msg = str(e.orig)
        
        if "users_email_key" in error_msg or "already exists" in error_msg:
            return ValidationResponse(success=False, message=f"Email '{validated_email}' is already registered.")
        
        return ValidationResponse(success=False, message="Database integrity constraint violation.")

    except Exception as e:
        db.session.rollback()
        logging.error(f"Gagal memproses pendaftaran user: {str(e)}")
        return ValidationResponse(success=False, message="An unexpected database error occurred.")

def normalize_and_validate_email(email_address):
    """
    Menormalisasi email untuk mencegah manipulasi alias (terutama Gmail).
    Contoh: 'andrew.twitter+youtube@gmail.com' -> 'andrew@gmail.com'
    """
    email_address = email_address.strip().lower()
    
    if '@' not in email_address:
        return None

    username_part, domain_part = email_address.split('@', 1)

    # Logika khusus untuk Gmail (gmail.com atau googlemail.com)
    if domain_part in ['gmail.com', 'googlemail.com']:
        # 1. Hapus semua teks setelah tanda plus (+) termasuk plus-nya sendiri
        username_part = username_part.split('+')[0]
        # 2. Hapus semua karakter titik (.) di dalam username Gmail
        username_part = username_part.replace('.', '')

    # Satukan kembali email yang sudah bersih
    cleaned_email = f"{username_part}@{domain_part}"
    return cleaned_email