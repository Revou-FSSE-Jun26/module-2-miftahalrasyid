from dataclasses import dataclass, field
@dataclass
class ValidationResponse:
    success: bool
    message: str
    status_code: int = field(default=400)
    
from app.services.user_service import get_all_users,add_new_users,get_user_by,update_user_by,ValidationResponse
from app.services.product_service import get_all_products, create_new_product, update_product, get_product_by_id, delete_product
from app.services.category_service import get_all_categories, get_category_by_id, create_category, update_category, delete_category
from app.services.order_service import get_all_orders, get_order_by_id, create_order, update_order, delete_order, get_order_items
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
    'get_product_by_id',
    'delete_product',
    'get_all_categories',
    'get_category_by_id',
    'create_category',
    'update_category',
    'delete_category',
    'get_all_orders',
    'get_order_by_id',
    'create_order',
    'update_order',
    'delete_order',
    'get_order_items',
]