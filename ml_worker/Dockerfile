FROM python:3.12-slim

WORKDIR /app

COPY ml_worker/requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ml_worker /app
COPY app /app/app
COPY model /app/model

CMD ["python", "main.py"]