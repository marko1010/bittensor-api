FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    pkg-config \
    libssl-dev \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m appuser
RUN mkdir -p /app/wallets && chown -R appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 