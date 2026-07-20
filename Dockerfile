# ─── Stage 1: build Vite frontend ───
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Django app ───
FROM python:3.12-slim
WORKDIR /app

# System deps for PyMuPDF + Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 mupdf-tools \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Pre-download rembg U2Net model (~170 MB)
RUN python -c "from rembg import remove; remove(b'')" 2>/dev/null || true

# App code
COPY . .
COPY --from=frontend /build/dist /app/frontend/dist

# Static + DB directory
RUN mkdir -p /app/staticfiles /app/data

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV DJANGO_SETTINGS_MODULE=djangoProject1.settings
ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/db.sqlite3

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
