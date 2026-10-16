# Use a small official Python runtime image.
FROM python:3.11-slim

# Avoid Python cache files and show logs immediately.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies before copying source code.
# Docker can reuse this layer when only code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and supporting files.
COPY app ./app
COPY data ./data
COPY frontend ./frontend
COPY scripts ./scripts

# Run the API as a non-root user.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Start the FastAPI backend.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]