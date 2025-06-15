from confluent_kafka import Consumer
from fastapi import FastAPI
import threading
import json
import requests
import psycopg2
from geopy.distance import geodesic
import statistics
import os

KAFKA_CONSUME_URL = "http://localhost:8100/consume"
KAFKA_TOPIC = "sensorvalues"
OPENSEARCH_URL = "http://localhost:9200"
OPENSEARCH_INDEX = "myindex"

app = FastAPI()

conf = {
    'bootstrap.servers': 'kafka:29092',
    'group.id': 'test-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe([KAFKA_TOPIC])

messages = []
actions = []

# Initial positions of sensors
init_positions = {
    1: (52.370216, 4.895168),
    2: (40.712776, -74.005974),
    3: (34.052235, -33.243683),
    4: (37.774929, -122.419416),
}

def fetch_opensearch_data(sensor_id):
    try:
        url = f"{OPENSEARCH_URL}/{OPENSEARCH_INDEX}/_search"
        query = {
            "size": 1000,
            "query": {
                "match": {
                    "id": str(sensor_id)
                }
            }
        }
        resp = requests.get(url, json=query)
        if resp.status_code == 200:
            data = resp.json()
            return [hit['_source'] for hit in data['hits']['hits']]
        else:
            print(f"OpenSearch query failed: {resp.text}")
            return []
    except Exception as e:
        print(f"OpenSearch error: {e}")
        return []


def fetch_postgres_metadata(sensor_id):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"), user=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"),
            host="localhost", port=os.getenv("POSTGRES_PORT", "5432")
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM sensors WHERE id = %s", (sensor_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result
    except Exception as e:
        print(f"PostgreSQL error: {e}")
        return None

# Compute distance from initial position
def compute_total_drift(sensor_id, historical_docs):
    if not historical_docs:
        return 0.0
    init_lat, init_long = init_positions[sensor_id]
    last = historical_docs[-1]
    current_lat = last['lat']
    current_long = last['long']
    return geodesic((init_lat, init_long), (current_lat, current_long)).meters

# Validate rules and push actions
def validate_rules(sensor_id, sensor_value, sensor_type, history):
    triggered = []

    # Rule 1: Distance drift
    drift = compute_total_drift(sensor_id, history)
    if drift > 1000:
        triggered.append(f"Maintenance: Sensor {sensor_id} drifted {int(drift)} meters")

    # Rule 2: Humidity threshold
    if sensor_type == 'humidity' and sensor_value > 80:
        triggered.append(f"Alert: Sensor {sensor_id} humidity too high: {sensor_value:.2f}%")

    # Rule 3: Value above 75th percentile
    if len(history) > 10 and sensor_type in ['temperature', 'humidity']:
        recent_vals = [h[sensor_type] for h in history if sensor_type in h]
        if recent_vals:
            p75 = statistics.quantiles(recent_vals, n=4)[2]
            if all(v > p75 for v in recent_vals[-5:]):
                triggered.append(f"Spike: Sensor {sensor_id} {sensor_type} persistently above 75th percentile")
    
    return triggered

def guard_maintenance_policy(message_value: str):
    try:
        message_dict = json.loads(message_value)
        sensor_id = int(message_dict.get("id"))
        sensor_value = float(message_dict.get("value"))
        timestamp = message_dict.get("timestamp")

        if sensor_id not in init_positions:
            print("ID not in known sensor list.")
            return

        # Try to infer sensor type
        sensor_type = "temperature" if sensor_value < 70 else "humidity"

        history = fetch_opensearch_data(sensor_id)
        metadata = fetch_postgres_metadata(sensor_id)

        rule_violations = validate_rules(sensor_id, sensor_value, sensor_type, history)

        for action in rule_violations:
            print(f"[Rule Triggered] {action}")
            actions.append({
                "sensor_id": sensor_id,
                "action": action,
                "timestamp": timestamp
            })

    except Exception as e:
        print(f"Error occurred: {e}")

def consume_loop():
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue

        value = msg.value().decode('utf-8')
        messages.append(value)
        print(f"Consumed: {value}")
        guard_maintenance_policy(value)

@app.get("/consume")
def get_messages():
    return {"messages": messages[-50:]}

@app.get("/actions")
def get_actions():
    return {"actions": actions[-50:]}

# Start Kafka consumer thread
threading.Thread(target=consume_loop, daemon=True).start()
