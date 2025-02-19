FROM python:3.11.4-slim-buster
LABEL manteiner="evila@student.42madrid.com"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && apt-get clean    \
    && rm -rf /varlib/lib/apt/lists/*

WORKDIR /app

COPY . /app/

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["./migrate.sh"]