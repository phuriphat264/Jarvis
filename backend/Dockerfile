FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y gcc \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt-get clean

COPY . .
