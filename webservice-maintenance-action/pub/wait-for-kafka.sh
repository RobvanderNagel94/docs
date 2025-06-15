#!/bin/sh
echo "⏳ Waiting for Kafka at $KAFKA_BOOTSTRAP_SERVERS..."
until nc -z kafka 29092; do
  sleep 15
done
echo "✅ Kafka is up - starting app"
exec uvicorn main:app --host 0.0.0.0 --port 8000