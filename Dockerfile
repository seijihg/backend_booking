# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
# Use --no-compile flag to skip bytecode compilation and save space during build
RUN pip install --user --no-cache-dir --no-compile -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 django

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/django/.local

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=django:django . .

# Switch to non-root user
USER django

# Make sure scripts in .local are usable
ENV PATH=/home/django/.local/bin:$PATH

# Create static directory with proper permissions
USER root
RUN mkdir -p /app/static && chown -R django:django /app/static
USER django

# Collect static files (with dummy env vars for build time)
RUN DJANGO_SECRET_KEY=dummy-key-for-build \
    DATABASE_URL=sqlite:///dummy.db \
    python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')"

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "120", "booking_api.wsgi:application"]
