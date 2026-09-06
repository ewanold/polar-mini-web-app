FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci
COPY src/frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend/src \
    POLAR_APP_HOST=0.0.0.0 \
    POLAR_APP_PORT=8000 \
    POLAR_APP_DATABASE_PATH=/app/database/polar-app.sqlite3
WORKDIR /app
COPY src/backend/ /app/backend/
COPY --from=frontend-build /build/frontend/dist/ /app/backend/src/polar_app/static/
RUN pip install --no-cache-dir /app/backend
RUN mkdir -p /app/database && chown -R 10001:10001 /app
USER 10001:10001
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"]
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn polar_app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
