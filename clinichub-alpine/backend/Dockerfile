FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache gcc g++ musl-dev linux-headers libffi-dev openssl-dev curl wget

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p logs

RUN addgroup -g 1000 clinichub && \
    adduser -D -s /bin/sh -u 1000 -G clinichub clinichub && \
    chown -R clinichub:clinichub /app

USER clinichub
EXPOSE 8001

CMD ["python", "server.py"]
