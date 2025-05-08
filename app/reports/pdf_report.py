from jinja2 import Environment, FileSystemLoader
import pdfkit, pandas as pd
from pathlib import Path
from ..config import Config
import os

TEMPLATE_DIR = Path(__file__).parent / 'templates'

def build_pdf(context: dict, out_file: Path):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    html = env.get_template('report.html').render(**context)
    
    # Use the correct path to wkhtmltopdf that exists on your system
    wkhtmltopdf_path = "/usr/local/bin/wkhtmltopdf"
    
    # Make sure the executable exists before using it
    if os.path.exists(wkhtmltopdf_path):
        pdfkit.from_string(html, str(out_file), configuration=pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path))
    else:
        raise FileNotFoundError(f"wkhtmltopdf executable not found at {wkhtmltopdf_path}. Please install it or update the path.")

def dataframe_to_excel(df: pd.DataFrame, out_file: Path):
    df.to_excel(out_file, index=True)
