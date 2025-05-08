import os
from pathlib import Path
import platform

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    CACHE_TYPE = "simple"
    
    # Set default wkhtmltopdf path based on OS
    if platform.system() == "Darwin":  # macOS
        # Common Homebrew installation paths
        POSSIBLE_PATHS = [
            "/usr/local/bin/wkhtmltopdf",
            "/opt/homebrew/bin/wkhtmltopdf",
            "/usr/bin/wkhtmltopdf"
        ]
        # Use the first path that exists
        WKHTMLTOPDF_PATH = next((path for path in POSSIBLE_PATHS if os.path.exists(path)), 
                               os.environ.get("WKHTMLTOPDF_PATH", "/usr/local/bin/wkhtmltopdf"))
    else:
        WKHTMLTOPDF_PATH = os.environ.get("WKHTMLTOPDF_PATH", "/usr/bin/wkhtmltopdf")
