import os
import json
import threading
from datetime import datetime
from confluent_kafka import Consumer
from fastapi import FastAPI
import requests
import psycopg2

KAFKA_TOPIC = "rawsensorvalues"
LAST_RUN_FILE = "last_runs.txt"
OPENSEARCH_URL = "http://localhost:9200"
OPENSEARCH_INDEX = "sensorindex"

messages = []
actions = []

app = FastAPI()

conf = {
    'bootstrap.servers': 'kafka:29092',
    'group.id': 'hourly-validator',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
}

consumer = Consumer(conf)
consumer.subscribe([KAFKA_TOPIC])


def log_run_time():
    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    with open(LAST_RUN_FILE, "a") as f:
        f.write(f"{now}\n")
    return now


def get_last_run_time():
    try:
        if not os.path.exists(LAST_RUN_FILE):
            return None
        with open(LAST_RUN_FILE, "r") as f:
            lines = f.readlines()
            if lines:
                return lines[-1].strip()
        return None
    except Exception as e:
        print(f"[ERROR] Could not read last run time: {e}")
        return None


def fetch_opensearch_data(sensor_id, from_time, to_time):
    try:
        url = f"{OPENSEARCH_URL}/{OPENSEARCH_INDEX}/_search"
        query = {
            "size": 1000,
            "query": {
                "bool": {
                    "must": [
                        {"match": {"id": str(sensor_id)}},
                        {"range": {
                            "ts": {
                                "gt": from_time,
                                "lt": to_time
                            }
                        }}
                    ]
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
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host="localhost",
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        cur = conn.cursor()
        cur.execute("SELECT id, type, unit, last_maintenance_date FROM sensors WHERE id = %s", (sensor_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result  # (id, type, unit, last_maintenance_date)
    except Exception as e:
        print(f"PostgreSQL error: {e}")
        return None


def validate_rules(sensor_id, sensor_type, unit, history, last_maintenance_date):
    triggered = []

    if not history:
        return triggered
    for doc in history:
        
        humidity = doc.get('humid')
        temperature = doc.get('temp')

        if humidity is not None and humidity > 80:
            triggered.append({
                "id": sensor_id,
                "rule": "High humidity > 80",
                "unit": unit,
                "type": doc.get('type', sensor_type),
                "lat": doc.get('lat'),
                "lon": doc.get('lon'),
                "last_maintenance_date": last_maintenance_date,
                "ts": doc.get('ts')
            })
            break

        if temperature is not None and temperature > 70:
            triggered.append({
                "id": sensor_id,
                "rule": "High temperature > 70",
                "unit": unit,
                "type": doc.get('type', sensor_type),
                "lat": doc.get('lat'),
                "lon": doc.get('lon'),
                "last_maintenance_date": last_maintenance_date,
                "ts": doc.get('ts')
            })
            break

    return triggered


def guard_maintenance_policy(message_value: str, from_time, to_time):
    try:
        data = json.loads(message_value)
        sensor_id = int(data.get("id"))
        timestamp = data.get("ts")

        if not sensor_id or not timestamp:
            print("[WARN] Incomplete Kafka message.")
            return

        metadata = fetch_postgres_metadata(sensor_id)
        if not metadata:
            print(f"[WARN] No metadata found for sensor {sensor_id}")
            return

        _, sensor_type, unit, last_maintenance_date = metadata
        history = fetch_opensearch_data(sensor_id, from_time, to_time)

        print(f"[DEBUG] Sensor {sensor_id} | Type: {sensor_type} | Events: {len(history)}")

        rule_hits = validate_rules(sensor_id, sensor_type, unit, history, last_maintenance_date)
        actions.extend(rule_hits)

        for rule in rule_hits:
            print(f"[TRIGGERED] {rule}")

    except Exception as e:
        print(f"[ERROR] Processing failed: {e}")


def consume_loop():
    last_time = get_last_run_time()
    now_time = log_run_time()

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[KAFKA ERROR] {msg.error()}")
            continue

        value = msg.value().decode("utf-8").strip()
        messages.append(value)
        print(f"[CONSUMED] {value}")
        guard_maintenance_policy(value, last_time or "1970-01-01T00:00:00Z", now_time)


@app.get("/consume")
def get_messages():
    return {"messages": messages[-50:]}


@app.get("/actions")
def get_actions():
    sorted_actions = sorted(actions[-50:], key=lambda x: x.get("ts", ""), reverse=True)
    return {"actions": sorted_actions}


threading.Thread(target=consume_loop, daemon=True).start()
