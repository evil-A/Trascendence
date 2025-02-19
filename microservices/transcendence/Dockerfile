FROM python:3.11.4-slim-buster

LABEL maintainer="evila@student.42madrid.com"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/

RUN pip3 install --upgrade pip --no-cache-dir -r requirements.txt

#RUN apt-get update && apt-get install -y build-essential libssl-dev
RUN pip3 install --no-cache-dir twisted[http2,tls]

COPY . /app/

CMD ["./migrate.sh"]
