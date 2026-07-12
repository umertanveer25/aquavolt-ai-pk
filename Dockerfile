# ──────────────────────────────────────────────────────────────────────────────
# AquaVolt-AI FastAPI Server — Dockerfile
# ──────────────────────────────────────────────────────────────────────────────
# Build:  docker build -t aquavolt-ai .
# Run:    docker run -p 8000:8000 --env-file .env aquavolt-ai
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.10-slim

# Metadata
LABEL maintainer="Umer Tanveer <umertanveer@awkum.edu.pk>"
LABEL description="AquaVolt-AI REST API — 19-satellite ensemble crop water-energy optimizer"
LABEL version="2.1.0"

# Set working directory
WORKDIR /app

# Install system dependencies for geospatial libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy production requirements first (Docker cache layer optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project source code
COPY api/ ./api/
COPY plugins/ ./plugins/
COPY dynamic_registry.py .
COPY ensemble_fusion.py .
COPY lstm_forecaster.py .

# Expose the FastAPI port
EXPOSE 8000

# Health check — confirms the API is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/'); assert r.status_code == 200" || exit 1

# Run the FastAPI server with Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
