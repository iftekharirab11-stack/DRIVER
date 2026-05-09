# Multi-stage Dockerfile for Alpha SaaS production deployment

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better caching
COPY project/frontend/package*.json ./
COPY project/frontend/tsconfig.json ./

RUN npm install

COPY project/frontend/src ./src
COPY project/frontend/public ./public
COPY project/frontend/vite.config.js ./

# Build the frontend
RUN npm run build

# Stage 2: Build backend
FROM python:3.9-slim AS backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-test.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Install frontend dependencies for production
WORKDIR /app/project/frontend
RUN npm install --production

# Stage 3: Final production image
FROM python:3.9-slim

WORKDIR /app

# Copy built frontend from frontend-builder
COPY --from=frontend-builder /app/frontend/dist ./project/frontend/dist

# Copy built backend from backend-builder
COPY --from=backend-builder /app .

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]