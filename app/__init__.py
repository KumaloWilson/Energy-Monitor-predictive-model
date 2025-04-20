from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import os

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Register blueprints
    from app.views.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    def index():
        return render_template('index.html')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
