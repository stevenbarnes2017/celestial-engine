from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from app.config import Config


db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, origins=["http://127.0.0.1:8000", "http://localhost:8000"])

    CORS(app)
    db.init_app(app)

    # Import models here so SQLAlchemy registers them
    from app.models.user import User

    # Register API Blueprints
    from app.api.auth import auth_bp
    from app.api.test_astro import test_bp  # <-- 1. ADD THIS IMPORT
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(test_bp)       # <-- 2. ADD THIS REGISTRATION

    with app.app_context():
        db.create_all()

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "global_free_beta": app.config['GLOBAL_FREE_BETA'],
            "engine": "Celestial Engine API v1.0"
        }), 200

    return app