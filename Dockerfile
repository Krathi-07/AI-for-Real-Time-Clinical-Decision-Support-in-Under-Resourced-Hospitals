# ============================================================
# Stage 1 — Builder
# Install all Python dependencies into an isolated venv.
# This stage has build tools (gcc, uv) that we don't want
# in the final image.
# ============================================================
FROM python:3.12-slim AS builder

# Install uv (Astral's fast package manager — same tool you use locally)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# System packages needed to compile some Python extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set uv environment variables
# UV_COMPILE_BYTECODE: pre-compiles .pyc files → faster cold starts
# UV_LINK_MODE=copy: avoids hardlink issues (same fix you applied locally)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build

# Copy dependency manifest first — Docker layer caches this separately.
# If only your source code changes (not pyproject.toml), Docker reuses
# the cached dependency layer and skips reinstalling everything.
COPY pyproject.toml uv.lock* ./

# Install all project dependencies into /opt/venv
RUN uv sync --frozen --no-install-project --no-dev

# Install the scispaCy biomedical NER model from the direct S3 URL.
# This cannot be listed in pyproject.toml (no PyPI entry), so we
# install it separately after the rest of the venv is ready.
RUN uv pip install \
    --python /opt/venv/bin/python \
    https://s3-us-west-2.amazonaws.com/ai2-s3-scispacy/releases/v0.5.4/en_ner_bc5cdr_md-0.5.4.tar.gz

# ============================================================
# Stage 2 — Runtime
# Lean final image: no build tools, no uv, no compiler.
# Only the venv, the source code, and Python itself.
# ============================================================
FROM python:3.12-slim AS runtime

# Copy the fully-built virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Make the venv's Python and scripts the default for all commands
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user — hospitals require this for security compliance
RUN useradd --create-home --shell /bin/bash clinicai

WORKDIR /app

# Copy source code (everything except what .dockerignore excludes)
COPY src/ ./src/

# Switch to non-root user before starting the server
USER clinicai

# Expose FastAPI's port
EXPOSE 8000

# Health check — Docker will probe this every 30s.
# If /health returns non-200 three times in a row, the container
# is marked unhealthy and orchestrators (Kubernetes, ECS) restart it.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start the FastAPI server
# --host 0.0.0.0: listen on all interfaces (required inside a container)
# --workers 2: two uvicorn processes — enough for a small hospital ward
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
