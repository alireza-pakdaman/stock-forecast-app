from pathlib import Path
import importlib.metadata as _meta
from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__, template_folder="web/templates",
                static_folder="web/static")
    app.config.from_object(Config)
    from .web.routes import bp as web_bp
    app.register_blueprint(web_bp)

    @app.get("/ping")
    def ping():
        return {
            "app": "stock-forecast-app",
            "version": _meta.version("Flask"),
            "status": "ok"
        }
    return app

app = create_app()
