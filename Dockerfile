# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install gunicorn
RUN pip install --no-cache-dir gunicorn

# Set workdir
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    REDIS_HOST="127.0.0.1" \
    REDIS_PORT=6379 \
    DNS_ADDRESS="0.0.0.0" \
    DNS_PORT=53 \
    WEB_ADDRESS="0.0.0.0" \
    WEB_PORT=8080

# Start the DNS/RemoteDict in the background, then run Gunicorn for the webapi
CMD ["/bin/sh", "-c", "python run_all_except_webapi.py & exec gunicorn nestiqdns.webapi:app --bind \"${WEB_ADDRESS}:${WEB_PORT}\" --workers 2"]
