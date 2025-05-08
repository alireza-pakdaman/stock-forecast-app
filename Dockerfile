FROM python:3.12-slim
RUN apt-get update && apt-get install -y build-essential git wget &&             wget -q https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb &&             apt-get install -y ./wkhtmltox_0.12.6-1.focal_amd64.deb &&             rm wkhtmltox_0.12.6-1.focal_amd64.deb &&             apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
ENV WKHTMLTOPDF_PATH=/usr/local/bin/wkhtmltopdf
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi:app"]
