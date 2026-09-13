# Use Debian-based slim Python runtime
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TESSERACT_CMD=/usr/bin/tesseract \
    PORT=5001 \
    OMP_THREAD_LIMIT=1 \
    OMP_NUM_THREADS=1 \
    MALLOC_ARENA_MAX=2 \
    RENDER=true

# Install system dependencies:
# - tesseract-ocr & tesseract-ocr-eng: Genuine local OCR engine and English training data
# - libzbar0: C library for pyzbar barcode decoding fallback
# - libgl1 & libglib2.0-0: System graphics libraries for headless image processing
# - curl: For container health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libzbar0 \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for dependencies
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code into /app/backend to match BASE_DIR (..) resolution
COPY . /app/backend/

# Ensure required runtime storage directories exist
RUN mkdir -p /app/uploads/annotated /app/data /app/reports

WORKDIR /app/backend

# Verify Tesseract installation and application imports at build time
RUN tesseract --version && \
    python -c "import pytesseract; print('pytesseract version:', pytesseract.__version__)" && \
    python -c "import app; print('LabelSure application loaded successfully')"

# Expose port (Render overrides with dynamic $PORT)
EXPOSE 5001

# Start Gunicorn server with 1 worker and 4 threads for low-memory container stability and fast responses
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 1 --threads 4 --timeout 180 app:app"]
