# File: gurbani-insight/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data and database directories
RUN mkdir -p data chroma_db

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_DB_PATH=/app/chroma_db
ENV PORT=8001

# Expose the application port
EXPOSE 8001

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]