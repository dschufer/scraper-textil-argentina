FROM python:3.11-slim

# Instalar dependencias del sistema para Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    wget \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Variable de entorno para que Playwright use el Chromium del sistema
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/bin
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright y apuntar al chromium del sistema
RUN pip install playwright && \
    playwright install-deps chromium && \
    playwright install chromium

COPY scraper.py .

CMD ["python", "scraper.py"]
