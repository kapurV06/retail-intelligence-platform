FROM python:3.11-slim

# Metadata
LABEL maintainer="varish@retail-intel"
LABEL description="Retail Inventory Intelligence Platform - Azure Deployment"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run data pipeline on build (generates analytics cache)
RUN python scripts/run_all.py || echo "Data already exists, skipping generation"

# Create streamlit config directory
RUN mkdir -p ~/.streamlit

# Streamlit configuration
RUN echo '\
[server]\n\
port = 8000\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
headless = true\n\
address = "0.0.0.0"\n\
\n\
[theme]\n\
base = "dark"\n\
primaryColor = "#00B4FF"\n\
backgroundColor = "#0A0E1A"\n\
secondaryBackgroundColor = "#0D1B2A"\n\
textColor = "#CBD5E1"\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
' > ~/.streamlit/config.toml

# Expose port 8000 (Azure App Service default)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/_stcore/health || exit 1

# Start the application
CMD ["streamlit", "run", "app.py", \
     "--server.port=8000", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
