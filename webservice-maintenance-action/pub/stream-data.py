import random
import time
from pydantic import BaseModel
import requests
import subprocess

KAFKA_PRODUCE_URL = "http://localhost:8100/produce"
OPENSEARCH_ADD_INDEX_URL = "http://localhost:8101/add-doc"
KAFKA_TOPIC = "rawsensorvalues"
OPENSEARCH_INDEX = "sensorindex"

sensor_types = ["vibration", "vibration", "pressure", "vibration"]
sensor_ids = [1, 2, 3, 4]

init_values = {
    1: {"value": 0.242, "temp": 20.0, "humid": 50.0, "lat": 52.370216, "lon": 4.895168, "ts": "2025-01-01T00:00:00Z"},
    2: {"value": 0.542, "temp": 21.0, "humid": 55.0, "lat": 40.712776, "lon": -74.005974, "ts": "2025-01-01T00:00:00Z"},
    3: {"value": 29.454, "temp": 22.0, "humid": 80.0, "lat": 34.052235, "lon": -33.243683, "ts": "2025-01-01T00:00:00Z"},
    4: {"value": 0.906, "temp": 19.0, "humid": 60.0, "lat": 37.774929, "lon": -122.419416, "ts": "2025-01-01T00:00:00Z"},
}

init_boundaries = {
    1: {"value": (-1, 1), "temp": (0, 50), "humid": (0, 60), "lat": (52.36, 52.38), "lon": (4.89, 4.91)},
    2: {"value": (-1, 1), "temp": (0, 50), "humid": (0, 100), "lat": (40.70, 40.73), "lon": (-74.01, -74.00)},
    3: {"value": (-50, 50), "temp": (0, 50), "humid": (0, 60), "lat": (34.05, 34.06), "lon": (-33.25, -33.24)},
    4: {"value": (-1, 1), "temp": (0, 50), "humid": (0, 60), "lat": (37.77, 37.78), "lon": (-122.42, -122.41)},
}

class KafkaEvent(BaseModel):
    id: str
    value: float
    ts: str

class OpensearchDocument(BaseModel):
    id: str
    lon: float
    lat: float
    humid: float
    temp: float
    ts: str

def create_topic():
    run = subprocess.run(["curl", "http://localhost:8100/create-topic"], capture_output=True, text=True)

def create_index():
    run = subprocess.run(["curl", "http://localhost:8101/create-index"], capture_output=True, text=True)

def random_value(sensor_id, field):
    low, high = init_boundaries[sensor_id][field]
    return round(random.uniform(low, high), 6)

def stream(event_count, delay):
    for i in range(event_count):
        sensor_id = random.choice(sensor_ids)
        
        value = random_value(sensor_id, "value")
        temp = random_value(sensor_id, "temp")
        humid = random_value(sensor_id, "humid")
        lat = random_value(sensor_id, "lat")
        lon = random_value(sensor_id, "lon")
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Send Kafka event (primary sensor measurement only)
        kafka_event = KafkaEvent(id=str(sensor_id), value=value, ts=ts)
        try:
            resp = requests.post(KAFKA_PRODUCE_URL, json=kafka_event.dict())
            resp.raise_for_status()
            print(f"[Kafka] Sent value={value:.3f} | id={sensor_id}, ts={ts}")
        except Exception as e:
            print(f"[Kafka] Error: {e}")

        # Send OpenSearch document (sensor internal state)
        os_doc = OpensearchDocument(id=str(sensor_id), lon=lon, lat=lat, humid=humid, temp=temp, ts=ts)
        try:
            resp = requests.post(OPENSEARCH_ADD_INDEX_URL, json=os_doc.dict())
            resp.raise_for_status()
            print(f"[OpenSearch] Indexed id={sensor_id}, ts={ts}, lon={lon}, lat={lat}, humid={humid}, temp={temp}")
        except Exception as e:
            print(f"[OpenSearch] Error: {e}")

        time.sleep(delay)

if __name__ == "__main__":
    create_topic()
    create_index()
    # Start streaming data
    stream(event_count=10000, delay=0.0)
