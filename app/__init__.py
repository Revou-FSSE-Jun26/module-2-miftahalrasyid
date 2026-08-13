import os
from flask import Flask,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
        db.create_all()


    from app.routes import v1_bp # prevent circular import on models
    app.register_blueprint(v1_bp)
    
    # You can still define a quick root home path directly here if you want
    @app.route('/')
    def home():
        return 'Welcome to Rovodev Shop api!'

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