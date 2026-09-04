# syntax=docker/dockerfile:1

# Etapa 1: compila o frontend React/Vite.
FROM node:20-alpine AS frontend-build
WORKDIR /build/frontend

# O frontend ainda não versiona package-lock.json; por isso o build usa npm install.
COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
# Em produção, quando VITE_API_URL não é informado, o frontend usa /api
# na mesma origem em que a página foi carregada.
RUN npm run test:unit && npm run test:quality && npm run build

# Etapa 2: imagem final do backend + frontend compilado.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8000 \
    FRONTEND_DIST_PATH=/app/frontend_dist

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 biblioavisa

COPY app/ ./app/
COPY database/ ./database/
COPY scripts/ ./scripts/
COPY --from=frontend-build /build/frontend/dist ./frontend_dist/

RUN mkdir -p /app/reports \
    && chown -R biblioavisa:biblioavisa /app

USER biblioavisa

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
