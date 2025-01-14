FROM python:3.10-slim

# Install system dependencies for mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files (if applicable)
RUN python manage.py collectstatic --no-input

# Expose port 8000 and run the app
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ReLog.wsgi:application"]
