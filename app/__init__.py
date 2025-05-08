from pathlib import Path
import importlib.metadata as _meta
from flask import Flask
from .config import Config
import logging
import os
import sys

def configure_logging():
    """Configure application-wide logging"""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        stream=sys.stdout
    )
    
    # Reduce verbosity of some loggers
    logging.getLogger('yfinance').setLevel(logging.WARNING)
    logging.getLogger('prophet').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {log_level} level")
    return logger

def create_app():
    # Configure logging first
    logger = configure_logging()
    
    # Create Flask app
    app = Flask(__name__, template_folder="web/templates",
                static_folder="web/static")
    app.config.from_object(Config)
    
    logger.info("Initializing Flask application")
    
    # Register blueprints
    from .web.routes import bp as web_bp
    app.register_blueprint(web_bp)
    
    @app.get("/ping")
    def ping():
        return {
            "app": "stock-forecast-app",
            "version": _meta.version("Flask"),
            "status": "ok"
        }
        
    logger.info("Flask application initialization complete")
    return app

app = create_app()
