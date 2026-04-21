FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set environment
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Initialize database (if DATABASE_URL is set, will use PostgreSQL)
RUN python backend/init_postgres.py || echo "DB init skipped (no DATABASE_URL)"

EXPOSE 5000

CMD gunicorn -w 2 -b 0.0.0.0:$PORT backend.app:app
