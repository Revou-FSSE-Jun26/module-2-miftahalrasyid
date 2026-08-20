from dataclasses import dataclass
@dataclass
class ValidationResponse:
    success: bool
    message: str
    
from app.services.user_service import get_all_users,add_new_users,get_user_by,update_user_by,ValidationResponse
from app.services.product_service import get_all_products, create_new_product, update_product, get_product_by_id
# Daftarkan semua fungsi servis yang ingin Anda ekspos ke folder luar



__all__ = [
    'get_all_users',
    'add_new_users',
    'get_user_by',
    'update_user_by',
    'ValidationResponse',
    'get_all_products',
    'create_new_product',
    'update_product',
    'get_product_by_id'
]