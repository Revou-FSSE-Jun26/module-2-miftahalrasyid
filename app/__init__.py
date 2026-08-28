import os
from datetime import timedelta
from flask import Flask, jsonify
from flask_smorest import Api
from dotenv import load_dotenv
from app.extensions import db, migrate, jwt

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["SQLALCHEMY_DATABASE_URI"]
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- JWT Configuration ---
    app.config['JWT_SECRET_KEY'] = os.environ["JWT_SECRET_KEY"]
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

    # --- Store Configuration ---
    app.config['TAX_PERCENT'] = float(os.environ.get("TAX_PERCENT", 11))
    app.config['CURRENCY'] = os.environ.get("CURRENCY", "IDR")

    # --- Swagger UI / Flask-Smorest Configuration ---
    app.config["API_TITLE"] = "Rovodev Shop API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://unpkg.com/swagger-ui-dist@5.32.13/"

    # --- Security scheme for Swagger UI (Bearer token input) ---
    app.config["API_SPEC_OPTIONS"] = {
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter your JWT token obtained from /auth/login or /auth/register"
                }
            }
        }
    }
    # app.config["API_SPEC_OPTIONS"] = {
    #     "components": {
    #         "securitySchemes": {
    #             "bearerAuth": {
    #                 "type": "oauth2",  # <-- Change from "http" to "oauth2"
    #                 "description": "Enter your credentials to log in automatically",
    #                 "flows": {
    #                     "password": {
    #                         # The absolute or relative URL to your login endpoint
    #                         "tokenUrl": "/auth/login", 
    #                         "scopes": {}
    #                     }
    #                 }
    #             }
    #         }
    #     }
    # }

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Initialize Smorest API
    api = Api(app)
    api.DEFAULT_ERROR_RESPONSE_NAME = None

    # CRUCIAL: Import all model files here so Alembic detects them
    with app.app_context():
        from app.models import User, Product, Order, Category, category_items, Order_item, Profile, Address
        try:
            db.session.execute(db.text('SELECT 1'))
            print("Database connection: OK")
        except Exception as e:
            print(f"Connection failed: {e}")

    # --- Register Smorest Blueprints (imported inside function to prevent circular imports) ---
    from app.routes import product_bp, users_bp, order_bp, auth_bp, category_bp
    from app.routes.v1.upload_routes_v1 import upload_bp
    from app.routes.v1.admin_routes_v1 import admin_bp
    from app.routes.v1.payment_routes_v1 import payment_bp

    api.register_blueprint(auth_bp)
    api.register_blueprint(users_bp)
    api.register_blueprint(product_bp)
    api.register_blueprint(order_bp)
    api.register_blueprint(category_bp)
    api.register_blueprint(upload_bp)
    api.register_blueprint(admin_bp)
    api.register_blueprint(payment_bp)
    print("Flask app initialized successfully.")

    # --- Static file serving for uploads (public, no auth) ---
    from flask import send_from_directory

    upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')

    @app.route('/uploads/<path:filepath>')
    def serve_upload(filepath):
        return send_from_directory(upload_folder, filepath)

    @app.route('/api')
    def home():
        return jsonify("message", 'Welcome to Rovodev Shop api!')

    return app
