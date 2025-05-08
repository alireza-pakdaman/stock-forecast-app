FROM python:3.11-slim

# Install dependencies and wkhtmltopdf
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    fontconfig \
    libfreetype6 \
    libjpeg62-turbo \
    libpng16-16 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    && wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1/wkhtmltox_0.12.6.1.bullseye_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1.bullseye_amd64.deb || true \
    && apt-get install -f -y \
    && rm wkhtmltox_0.12.6.1.bullseye_amd64.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WKHTMLTOPDF_PATH=/usr/local/bin/wkhtmltopdf

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi:app"]
