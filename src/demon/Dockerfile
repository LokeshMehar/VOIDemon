# Build stage
FROM python:3.9-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/root/.local/bin:$PATH

# Create non-root user
RUN groupadd -r demon && useradd -r -g demon demon

WORKDIR /app

# Copy application files
COPY --chown=demon:demon demon.py node.py ./

USER demon

EXPOSE 5000

CMD ["python", "-u", "demon.py"]