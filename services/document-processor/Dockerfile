FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libreoffice \
    pandoc \
    curl \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY . .

# Create non-root user and set permissions
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

# Note: NLTK dependencies removed since we're using LLaVA + Whisper approach instead of LlamaParse

CMD ["python", "simple_processor.py"]