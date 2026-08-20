# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (specifically tesseract-ocr)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose the default port (Render dynamically assigns $PORT)
EXPOSE 5001

# Run gunicorn and bind to the PORT environment variable (default 5001)
CMD gunicorn --timeout 120 --workers 1 --threads 2 --bind 0.0.0.0:${PORT:-5001} app:app
