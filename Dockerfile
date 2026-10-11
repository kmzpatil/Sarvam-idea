# ==============================================================================
# Multi-Stage Production Dockerfile for Signal Fusion Board
# Stage 1: Build React 19 Frontend
# Stage 2: Serve FastAPI + Compiled Frontend Single-Port on Python 3.12
# ==============================================================================

FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.12-slim AS runner
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend and Tests
COPY backend/ ./backend/
COPY tests/ ./tests/
COPY pytest.ini ./

# Copy compiled frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Start FastAPI server
CMD ["sh", "-c", "python -m uvicorn backend.app:app --host 0.0.0.0 --port ${PORT}"]
