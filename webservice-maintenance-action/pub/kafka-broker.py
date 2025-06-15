from fastapi import FastAPI, HTTPException
from confluent_kafka import Producer, admin
from pydantic import BaseModel
import socket

app = FastAPI()

KAFKA_URL = "kafka:29092"
KAFKA_TOPIC = "rawsensorvalues"

# Kafka configuration
producer = Producer({
    "bootstrap.servers": KAFKA_URL,
    "client.id": socket.gethostname()
})

class KafkaEvent(BaseModel):
    id: str
    value: float
    ts: str

class TopicRequest(BaseModel):
    topic_name: str = KAFKA_TOPIC
    num_partitions: int = 1
    replication_factor: int = 1

@app.post("/produce")
def produce_event(event: KafkaEvent):
    """Produce a message to Kafka."""
    try:
        producer.produce(KAFKA_TOPIC, key=event.id, value=event.json())
        producer.flush()
        return {"status": "sent", "message": event.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-topic")
def create_kafka_topic(request: TopicRequest):
    """Create a Kafka topic."""
    try:
        admin_client = admin.AdminClient({"bootstrap.servers": KAFKA_URL})
        new_topic = admin.NewTopic(
            request.topic_name,
            num_partitions=request.num_partitions,
            replication_factor=request.replication_factor
        )
        fs = admin_client.create_topics([new_topic])
        for _, f in fs.items():
            f.result()
        return {"status": "created", "topic": request.topic_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
