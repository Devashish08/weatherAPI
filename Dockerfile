# Python Flask application Dockerfile

FROM python:3.9-slim

# Ensures Python output is sent straight to the terminal
ENV PYTHONUNBUFFERED=True

# Set working directory for the application
ENV APP_HOME=/app
WORKDIR $APP_HOME

# Copy and install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY . .

# Expose the port the app runs on
# Google Cloud Run provides the PORT env var, defaults to 8080.
EXPOSE 8080

# Define the command to run the application
# Gunicorn binds to all interfaces on $PORT (default 8080).
# --workers and --threads are configured for typical I/O-bound app on Cloud Run.
# --timeout 0 defers to Cloud Run's own request timeout.
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 0 app:app