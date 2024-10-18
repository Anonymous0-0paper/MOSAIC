# Base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt
RUN pip install python-dotenv  # Install python-dotenv to load the .env file

# Copy project and .env file
COPY . /app/
COPY .env /app/.env

# Expose port
EXPOSE 8000

# Command to run the app
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "myproject.wsgi:application"]
