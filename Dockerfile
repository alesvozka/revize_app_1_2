FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default jen pro lokální/dev prostředí – v produkci přepiš env proměnnou SECRET_KEY
ENV SECRET_KEY="change_me_to_random_string"

EXPOSE 8000

# Na Railway / PaaS vezme port z env PORT, lokálně běží na 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
