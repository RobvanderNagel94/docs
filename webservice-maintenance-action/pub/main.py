from fastapi import FastAPI
from confluent_kafka import Producer
import socket

topic = "sensorvalues"

app = FastAPI()

conf = {
    'bootstrap.servers': 'kafka:29092',
    'client.id': socket.gethostname()
}
producer = Producer(conf)

@app.post("/produce")
def produce(message: str):
    try:
        producer.produce(topic, key='key', value=message)
        producer.flush()
        return {"status": "sent", "message": message}
    except Exception as e:
        return {"status": "error", "detail": str(e)}