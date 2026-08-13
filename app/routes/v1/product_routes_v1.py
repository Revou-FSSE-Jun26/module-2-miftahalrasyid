from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.schemas import ProductSchema
# product_bp = Blueprint('products', __name__)

product_bp = Blueprint(
    'products', 
    __name__, 
    url_prefix='/api/v1/products', 
    description='Operasi Data Produk (Products - Mock Data)'
)

products_mock_data = [
    {"id": 1, "name": "Laptop", "brand": "Generic", "price": 15000000, "quantity": 10, "user_id": 1},
    {"id": 2, "name": "Mouse", "brand": "Generic", "price": 250000, "quantity": 50, "user_id": 1},
    {"id": 3, "name": "Keyboard", "brand": "Generic", "price": 500000, "quantity": 30, "user_id": 1},
    {"id": 4, "name": "Monitor", "brand": "Generic", "price": 3500000, "quantity": 15, "user_id": 1}
]

@product_bp.route('/')
class ProductsRoot(MethodView):

    # Marshmallow otomatis menyaring array dictionary biasa ini agar pas dengan skema output
    @product_bp.response(200, ProductSchema(many=True))
    def get(self):
        """Mengambil semua daftar produk (Mock Data)"""
        return products_mock_data

    @product_bp.arguments(ProductSchema, location="form")
    @product_bp.response(201, ProductSchema)
    def post(self, product_instance):
        """Menambahkan produk baru ke dalam memori array sementara"""
        # Karena load_instance=True di schema, product_instance sudah berupa objek SQLAlchemy Model.
        # Untuk data tiruan, kita konversi balik menjadi dict agar bisa di-append ke array Anda.
        new_product_dict = {
            "id": len(products_mock_data) + 1,
            "name": product_instance.name,
            "brand": product_instance.brand,
            "price": float(product_instance.price),
            "quantity": product_instance.quantity,
            "user_id": product_instance.user_id
        }
        products_mock_data.append(new_product_dict)
        return product_instance

@product_bp.route('/<int:id>')
class ProductDetail(MethodView):

    @product_bp.response(200, ProductSchema)
    def get(self, id):
        """Mengambil detail produk berdasarkan ID (Mock Data)"""
        # Menggunakan logika pencarian 'next' andalan Anda
        has_product = next((product for product in products_mock_data if product["id"] == id), None)
        
        if not has_product:
            # Menggunakan abort milik Smorest dengan parameter 'message'
            abort(404, message="Product is not found")
            
        return has_product