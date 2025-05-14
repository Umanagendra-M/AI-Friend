FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if needed

RUN apt-get update && \
    apt-get install -y build-essential ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
    
# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directory for shared files
RUN mkdir -p /app/shared

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "app.py"]