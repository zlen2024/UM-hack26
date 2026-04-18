FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV NEXT_TELEMETRY_DISABLED=1

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install frontend dependencies
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci

# Copy application code
COPY backend backend/
COPY frontend frontend/

# Build frontend
RUN cd frontend && npm run build

# Create start script
RUN echo '#!/bin/bash\n\
cd /app/backend\n\
uvicorn main:app --host 127.0.0.1 --port 8000 &\n\
cd /app/frontend\n\
exec npm start\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port and start
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
CMD ["/app/start.sh"]
