# ---- build stage: install dependencies into a venv ----
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- runtime stage: copy only the venv + app code, no build tools ----
FROM python:3.12-slim

RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ARG VERSION=dev
ARG COMMIT=unknown
ARG BUILD_DATE=unknown

ENV APP_VERSION=$VERSION
ENV GIT_COMMIT=$COMMIT
ENV BUILD_DATE=$BUILD_DATE
WORKDIR /app
COPY app ./app

EXPOSE 8000

# Overridden by docker-compose/Kubernetes for the worker and beat processes.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
