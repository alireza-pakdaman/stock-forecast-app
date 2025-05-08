FROM python:3.11-slim

# Install essential dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    fontconfig \
    libx11-6 \
    libxext6 \
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf using a simpler method
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
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
ENV WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf
ENV LOG_LEVEL=INFO

# Set up wrapper script for xvfb (needed for wkhtmltopdf in headless environments)
RUN echo '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf "$@"' > /usr/bin/wkhtmltopdf-xvfb \
    && chmod +x /usr/bin/wkhtmltopdf-xvfb \
    && ln -s /usr/bin/wkhtmltopdf-xvfb /usr/local/bin/wkhtmltopdf

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi:app", "--timeout", "120", "--log-level", "info"]
