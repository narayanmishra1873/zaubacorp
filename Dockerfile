# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by Playwright and for general utility
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright specific dependencies
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxrender1 \
    libfontconfig1 \
    libxss1 \
    libxtst6 \
    # Additional dependencies for headless browsers
    xvfb \
    fonts-liberation \
    # Clean up apt cache
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and their OS dependencies
RUN playwright install --with-deps chromium

# Copy the application source code into the container at /app/src
COPY src/ ./src/

# Expose port 8000 to the outside world (as configured in server.py)
EXPOSE 8000

# Define environment variable for GOOGLE_API_KEY (user will set this in the hosting platform)
# ENV GOOGLE_API_KEY="your_google_api_key_here"

# Command to run the application
CMD ["python", "src/server.py"]
