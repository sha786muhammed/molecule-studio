FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    STUDIO_DEMO=1 \
    STUDIO_DATA_DIR=/tmp/molecule-studio
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 libstdc++6 libxrender1 libxext6 libx11-6 libexpat1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 studio
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=studio:studio backend ./backend
RUN python -c "from backend.chemistry import prepare_molecule; from tblite.interface import Calculator; assert prepare_molecule('O')['formula'] == 'H2O'"
COPY --from=frontend --chown=studio:studio /build/dist/client ./dist/client
USER studio
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn backend.hosted:create_hosted_app --factory --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --limit-concurrency 32 --backlog 64"]
