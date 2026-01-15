FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies for I2C/SPI and NFC
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libi2c-dev \
    i2c-tools \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY cli.py .

# Create non-root user with access to I2C/SPI devices
RUN groupadd -g 997 i2c || true && \
    groupadd -g 998 spi || true && \
    useradd -m -u 1000 -G i2c,spi nfcuser || true

# Set permissions
RUN chown -R nfcuser:nfcuser /app

# Switch to non-root user (will be overridden by docker-compose for device access)
USER nfcuser

# Default command
CMD ["python3", "cli.py", "daemon"]
