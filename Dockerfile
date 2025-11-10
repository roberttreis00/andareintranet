FROM python:3.11-slim-bookworm

# Instalar locale pt_BR.UTF-8 antes de qualquer coisa
RUN apt-get update && apt-get install -y locales \
    && sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen pt_BR.UTF-8

# Definir variáveis de ambiente de locale
ENV LANG=pt_BR.UTF-8
ENV LANGUAGE=pt_BR:pt
ENV LC_ALL=pt_BR.UTF-8

# Define diretório de trabalho no container
WORKDIR /app

COPY requirements.txt /app/

# Instala dependências necessárias para Django + MySQL/MariaDB
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    python3-dev \
    pkg-config \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libmariadb-dev \
    libmariadb-dev-compat \
 && rm -rf /var/lib/apt/lists/*

# Atualiza pip e instala dependências Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Instala netcat (usado em scripts de healthcheck/startup)
RUN apt-get update && apt-get install -y netcat-open
