FROM python:3.12-slim

WORKDIR /app

# Install dependencies (use tsinghua mirror for speed in China)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy full project (maintains original directory structure)
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY data/ ./data/

EXPOSE 5000

WORKDIR /app/backend
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
