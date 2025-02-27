FROM python:3.10-slim

# Установка системных библиотек
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
