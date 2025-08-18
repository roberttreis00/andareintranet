FROM python:3.11-slim-bookworm

# Define diretório de trabalho no container
WORKDIR /app

COPY requirements.txt /app/

# Instala dependências
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    python3-dev \
    pkg-config \
    build-essential \
    libssl-dev \
    libffi-dev \
    libmariadb-dev \
    libmariadb-dev-compat \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y netcat-openbsd

COPY . /app/
