# Use an official Python runtime as a parent image
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the entire application code
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=app.py
EXPOSE 5000

# Default command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
