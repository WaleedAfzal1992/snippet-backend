# Use a Debian-based Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Update system and install pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input

# Expose the default Django port
EXPOSE 8000

# Start the Django app
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
