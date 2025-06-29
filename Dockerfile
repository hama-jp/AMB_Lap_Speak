FROM python:3.7-alpine

RUN apk add --no-cache gcc musl-dev mariadb-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
