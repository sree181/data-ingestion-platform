FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy RL optimization code (needed for model loading)
COPY ../../rl_optimization /app/rl_optimization

# Copy service code
COPY . /app/

# Expose port
EXPOSE 8013

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013"]

