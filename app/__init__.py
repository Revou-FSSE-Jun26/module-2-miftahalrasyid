import os
from flask import Flask,jsonify,Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from dotenv import load_dotenv
from flask_smorest import Api

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- 3. Konfigurasi Swagger UI Flask-Smorest ---
    app.config["API_TITLE"] = "Rovodev Shop API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    
    # Menentukan URL halaman dokumentasi Swagger Anda
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    
    # CRITICAL: Menggunakan unpkg CDN versi 4 agar tampilan UI ter-render sempurna & modern
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://unpkg.com/swagger-ui-dist@5.32.13/"

    # Inisialisasi Platform Smorest API
    api = Api(app)

    db.init_app(app)
    migrate.init_app(app, db)
    # CRUCIAL: Import all separate files here so Alembic detects them!
    with app.app_context():
        from app.models import User, Product, Order, Category, category_items, order_items
        try:
            db.session.execute(db.text('SELECT 1'))
            print("Database connection: OK")
        except Exception as e:
            print(f"Connection failed: {e}")
        # before setup flask-migrate 
        # db.create_all()

# --- 4. Registrasi Blueprint Smorest (Trik Mencegah Circular Import) ---
    # Melakukan import blueprint di dalam fungsi setelah db terbentuk
    from app.routes import product_bp,users_bp,order_bp
    
    # Daftarkan blueprint user ke dalam engine Smorest
    api.register_blueprint(users_bp)
    api.register_blueprint(product_bp)
    api.register_blueprint(order_bp)

    # from app.routes import v1_bp # prevent circular import on models
    # api = Blueprint('api', __name__, url_prefix='/api')

    # api.register_blueprint(v1_bp)

    @app.route('/api')
    def home():
        return jsonify("message",'Welcome to Rovodev Shop api!')
    
    # app.register_blueprint(api)
    
    # You can still define a quick root home path directly here if you want

    @app.errorhandler(500)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": "Method Not Allowed",
            "message": error.description,
            "status_code": 500
        }), 500
    
    @app.errorhandler(400)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": "Bad Request",
            "message": error.description,
            "status_code": 400
        }), 400
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": "Method Not Allowed",
            "message": "The HTTP method used is not supported for this endpoint.",
            "status_code": 405
        }), 405

    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({
            "success": False,
            "error": "Not Found",
            "message": error.description,
            "status_code": 404
        }), 404
        
    return app