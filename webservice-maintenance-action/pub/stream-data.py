import numpy as np
import random
import time
import pydantic
import requests
import subprocess
import os

KAFKA_PRODUCE_URL = "http://localhost:8100/produce"
KAFKA_TOPIC = "sensorvalues"
OPENSEARCH_URL = "http://localhost:9200"
OPENSEARCH_INDEX = "myindex"

# Initial state for each sensor
init_position = {
    1: {"lat": 52.370216, "long": 4.895168},
    2: {"lat": 40.712776, "long": -74.005974},
    3: {"lat": 34.052235, "long": -33.243683},
    4: {"lat": 37.774929, "long": -122.419416},
}

# Initial values (base) for drifting fields
sensor_values = {
    1: {"temperature": 20.0, "humidity": 50.0},
    2: {"temperature": 21.0, "humidity": 55.0},
    3: {"temperature": 22.0, "humidity": 45.0},
    4: {"temperature": 23.0, "humidity": 60.0},
}

# Example drift configuration
simulate = {
    1: {"drift": "high", "fields": ["lat", "long"]},
    2: {"drift": "high", "fields": ["temperature", "humidity"]},
    3: {"drift": "low", "fields": ["temperature"]},
    4: {"drift": "low", "fields": ["humidity"]},
}

class KafkaEvent(pydantic.BaseModel):
    id: str
    value: float
    timestamp: str

class OpensearchDocument(pydantic.BaseModel):
    id: str
    long: float
    lat: float
    humidity: float
    temperature: float
    timestamp: str

def generate_value(sensor_id, step, field):
    base = sensor_values[sensor_id][field]
    drift_level = simulate[sensor_id]["drift"] if field in simulate[sensor_id]["fields"] else "none"

    if drift_level == "high":
        delta = np.random.normal(loc=0.1, scale=0.05)
    elif drift_level == "low":
        delta = np.random.normal(loc=0.02, scale=0.01)
    else:
        delta = np.random.normal(loc=0.0, scale=0.005)

    value = base + delta
    # Keep values within sensible range
    if field == "humidity":
        value = max(0.0, min(100.0, value))
    elif field == "temperature":
        value = max(-50.0, min(100.0, value))

    sensor_values[sensor_id][field] = value
    return value

def update_position(sensor_id, lat, long):
    drift_level = simulate[sensor_id]["drift"] if "lat" in simulate[sensor_id]["fields"] else "none"
    if drift_level == "high":
        step_lat = random.uniform(-0.01, 0.01)
        step_long = random.uniform(-0.02, 0.02)
    elif drift_level == "low":
        step_lat = random.uniform(-0.001, 0.001)
        step_long = random.uniform(-0.001, 0.001)
    else:
        step_lat = random.uniform(-0.0001, 0.0001)
        step_long = random.uniform(-0.0001, 0.0001)
    return lat + step_lat, long + step_long

def create_index():
    url = f"{OPENSEARCH_URL}/{OPENSEARCH_INDEX}"
    resp = requests.put(url, json={
        "settings": {"number_of_shards": 1, "number_of_replicas": 0}
    })
    print(f"[OpenSearch] Index creation: {resp.status_code} {resp.text}")

def create_topic():
    try:
        result = subprocess.run(
            ["docker", "exec", "kafka", "kafka-topics", "--list", "--bootstrap-server", "localhost:9092"],
            capture_output=True, text=True
        )
        if KAFKA_TOPIC not in result.stdout:
            subprocess.run([
                "docker", "exec", "kafka", "kafka-topics", "--create",
                "--bootstrap-server", "localhost:9092",
                "--replication-factor", "1", "--partitions", "1",
                "--topic", KAFKA_TOPIC
            ])
            print(f"Kafka topic '{KAFKA_TOPIC}' created.")
        else:
            print(f"Kafka topic '{KAFKA_TOPIC}' already exists.")
    except Exception as e:
        print(f"Error managing Kafka topic: {e}")

def stream(event_count):
    sensor_ids = list(init_position.keys())

    for i in range(1, event_count + 1):
        sensor_id = random.choice(sensor_ids)

        # Update position
        pos = init_position[sensor_id]
        new_lat, new_long = update_position(sensor_id, pos["lat"], pos["long"])
        init_position[sensor_id]["lat"] = new_lat
        init_position[sensor_id]["long"] = new_long

        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Generate sensor values
        temp_val = generate_value(sensor_id, i, "temperature")
        humidity_val = generate_value(sensor_id, i, "humidity")

        # Send Kafka events
        for val in [("temperature", temp_val), ("humidity", humidity_val)]:
            event = KafkaEvent(id=str(sensor_id), value=float(val[1]), timestamp=timestamp)
            kafka_resp = requests.post(KAFKA_PRODUCE_URL, params={"message": event.json()})
            if kafka_resp.status_code == 200:
                print(f"[Kafka] Sent {val[0]} event: {event.json()}")
            else:
                print(f"[Kafka] Failed to send {val[0]} event: {kafka_resp.text}")

        # Send to OpenSearch
        os_doc = OpensearchDocument(
            id=str(sensor_id),
            lat=new_lat,
            long=new_long,
            temperature=float(temp_val),
            humidity=float(humidity_val),
            timestamp=timestamp
        )
        doc_id = f"{sensor_id}-{i}"
        os_url = f"{OPENSEARCH_URL}/{OPENSEARCH_INDEX}/_doc/{doc_id}"
        os_resp = requests.post(os_url, json=os_doc.dict())
        if os_resp.status_code in (200, 201):
            print(f"[OpenSearch] Indexed doc: {doc_id}")
        else:
            print(f"[OpenSearch] Failed to index doc: {os_resp.text}")

        # Optional delay
        # time.sleep(0.1)

if __name__ == "__main__":
    create_index()
    create_topic()
    stream(event_count=10000)

