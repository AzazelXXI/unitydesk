FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy project
COPY . .

# Command to run the application
CMD ["uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "key.pem", "--ssl-certfile", "cert.pem"]
