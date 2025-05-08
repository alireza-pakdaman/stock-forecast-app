from jinja2 import Environment, FileSystemLoader
import pdfkit, pandas as pd
from pathlib import Path
from ..config import Config
import os
import logging

logger = logging.getLogger(__name__)
TEMPLATE_DIR = Path(__file__).parent / 'templates'

def build_pdf(context: dict, out_file: Path):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    html = env.get_template('report.html').render(**context)
    
    # Get the path from environment variable or use default
    wkhtmltopdf_path = os.environ.get('WKHTMLTOPDF_PATH', '/usr/bin/wkhtmltopdf')
    logger.info(f"Using wkhtmltopdf path: {wkhtmltopdf_path}")
    
    # Configure options for better compatibility in cloud environments
    options = {
        'quiet': '',
        'no-outline': None,
        'encoding': 'UTF-8',
        'enable-local-file-access': None
    }
    
    try:
        # Make sure the executable exists before using it
        if os.path.exists(wkhtmltopdf_path):
            pdfkit.from_string(html, str(out_file), 
                              configuration=pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path),
                              options=options)
            logger.info(f"PDF successfully generated at {out_file}")
        else:
            error_msg = f"wkhtmltopdf executable not found at {wkhtmltopdf_path}"
            logger.error(error_msg)
            with open(str(out_file), 'w') as f:
                f.write("PDF Generation Error: wkhtmltopdf not found")
            logger.info("Created error placeholder PDF")
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        # Create a basic error file instead of failing completely
        with open(str(out_file), 'w') as f:
            f.write(f"PDF Generation Error: {str(e)}")
        logger.info("Created error placeholder PDF due to exception")

def dataframe_to_excel(df: pd.DataFrame, out_file: Path):
    df.to_excel(out_file, index=True)
