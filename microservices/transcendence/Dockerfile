FROM python:3.11.4-slim-buster
LABEL manteiner="evila@student.42madrid.com"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    openssl \
    && apt-get clean    \
    && rm -rf /varlib/lib/apt/lists/* 

WORKDIR /app

COPY . /app/

RUN openssl req -newkey rsa:4096 -x509 -sha256 -days 365 -nodes \
       		-out /cert.pem \
       		-keyout /key.pem \
       		-subj "/C=ES/ST=Madrid/L=Madrid/O=42 School/OU=amorion-/CN=localhost/"

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["./migrate.sh"]