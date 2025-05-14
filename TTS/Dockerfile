FROM python:3.9-alpine3.15

# Add a non-root user
RUN adduser -D -u 1000 app

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg (for Alpine)
RUN apk add --no-cache ffmpeg

# Copy all files
COPY . .

# Create directory for shared_tts
RUN python -c "import os; os.makedirs('/app/shared_tts', exist_ok=True)"

# Uncomment to run as non-root user
#USER app

# Start the application using gunicorn
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8003", "app:app"]
