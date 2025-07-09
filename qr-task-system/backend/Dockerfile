FROM python:3.11-slim

WORKDIR /app

# Copy everything from backend into /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
