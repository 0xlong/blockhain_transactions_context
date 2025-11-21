# Dockerfile - Instructions to build a container image of your app
# Think of it as a recipe that tells GCP how to set up and run your app

# Start from a base image that has Python 3.11 pre-installed
# This is like starting with a clean computer that already has Python
FROM python:3.11-slim

# Set the working directory inside the container
# All subsequent commands will run from this directory
WORKDIR /app

# Install system dependencies that some Python packages need
# These are low-level libraries for Chrome (needed by Selenium)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chrome/Selenium
# This tells Selenium where to find the Chrome browser
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Copy requirements.txt first (before other files)
# This is a Docker optimization: if requirements.txt doesn't change,
# Docker can reuse the cached layer and skip reinstalling packages
COPY requirements.txt .

# Install all Python dependencies from requirements.txt
# --no-cache-dir saves space by not storing download cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
# This includes streamlit_app.py, modules/, pages/, etc.
COPY . .

# Expose port 8080 (Cloud Run expects apps to listen on this port)
# This is like opening a door for incoming traffic
EXPOSE 8080

# The command that runs when the container starts
# This starts your Streamlit app on port 8080, accessible from any IP (0.0.0.0)
# --server.enableCORS=false and --server.enableXsrfProtection=false are needed for Cloud Run
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]

