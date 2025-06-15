---
layout: default
title: Microservice
---

## Examples

A microservice that runs every $2$ minute(s)  to identify sensors needing maintenance actions on these rules:

- **Rule A**: Sensor has moved more than 3000 meters since init location.

- **Rule B**: Sensor values exceed the 75th percentile for more than 20 datapoints in a row.

- **Rule C**: Sensor humidity exceeds when relative humidity level > 80% for more than 20 datapoints in a row.

The service outputs sensor IDs requiring maintenance along with the triggering rule (A, B, or C).


### Method
For a set of sensors indexed by $i = 1, 2, 3, 4$. Let the output of each sensor at time $t$ be represented as:

$$
\text{Sensor}_i(t) = \{ \text{id}_i, \text{type}_i, \text{location}_i(t), \text{humidity}_i(t), \text{temperature}_i(t), \text{value}_i(t), \text{timestamp}_i(t) \}
$$

where:
- $\text{id}_i$ is the unique identifier (kafka, opensearch, postgres)
- $\text{type}_i$ is the sensor type (postgres),
- $\text{location}_i(t) = (\text{long}_i(t), \text{lat}_i(t))$ is the geographic position at time $t$ (opensearch),
- $\text{humidity}_i(t)$ is the humidity level at time $t$ (opensearch),
- $\text{temperature}_i(t)$ is the temperature level at time $t$ (opensearch),
- $\text{value}_i(t)$ is the sensor reading at time $t$ (kafka),
- $\text{timestamp}_i(t)$ is the time of the reading (kafka).

Note that there are three DB involved; 
- **kafka** (sensor), 
- **postgres** (meta sensor), 
- **opensearch** (location & environment sensor). 

Basically, the sensor sends data to two bigdata stores. Metadata of the sensor and their last maintenance data is stored in postgres.

**Example static Postgres**

```
id, type, last_maintenance_date
(1, 'vibration', '2023-01-01T00:00:00Z'),
(2, 'humidity', NULL),
(3, 'temperature', '2022-04-01T00:00:00Z'),
(4, 'pressure', '2023-05-15T12:30:00Z'),
```

**Example stream to Kafka**
```
{"id": 1, "value": 0.123, "timestamp": "2025-01-01T00:00:00Z"}
```
to a kafka broker on topic name `"sensorvalues"`.

**Example stream to Opensearch**
```
{"id": 1, "long": 4.895168, "lat": 52.370216, "humidity": 82.5, "temperature": 20.0, "timestamp": "2025-01-01T00:00:00Z"}
```

to a opensearch broker on name `"myindex"`.

---

**Infra**

.env
```
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=mydb
POSTGRES_VERSION=latest

OPENSEARCH_INITIAL_ADMIN_PASSWORD=A8n@1428S
OPEN_SEARCH_VERSION=2.14.0
KAFKA_VERSION=7.4.0
ZOOKEEPER_VERSION=latest
```

docker-compose.yml

```docker-compose
services:

  zookeeper:
    image: bitnami/zookeeper:${ZOOKEEPER_VERSION}
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ALLOW_ANONYMOUS_LOGIN: yes

  kafka:
    image: confluentinc/cp-kafka:${KAFKA_VERSION}
    container_name: kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_INTERNAL:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT_INTERNAL://kafka:29092
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,PLAINTEXT_INTERNAL://0.0.0.0:29092
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT_INTERNAL
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper

  opensearch:
    image: opensearchproject/opensearch:${OPEN_SEARCH_VERSION}
    container_name: opensearch
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true
      - bootstrap.memory_lock=true
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=${OPENSEARCH_INITIAL_ADMIN_PASSWORD}
    ulimits:
      memlock:
        soft: -1
        hard: -1
    ports:
      - "9200:9200"
    volumes:
      - opensearch-data:/usr/share/opensearch/data

  postgres:
    image: postgres:${POSTGRES_VERSION}
    container_name: postgres
    restart: always
    env_file: .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5433:5432"

volumes:
  opensearch-data:
  postgres-data:
```

docker compose --env-file .env up --build

Then, add the fields for sensors in postgres:

docker exec -it postgres sh \
psql -h localhost -p 5432 -U user -d mydb\
$:

Now add the following:

```sql
CREATE TABLE sensors (
    id INTEGER PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    last_maintenance_date TIMESTAMP NULL
);

INSERT INTO sensors (id, type, last_maintenance_date) VALUES
    (1, 'vibration', '2023-01-01T00:00:00Z'),
    (2, 'humidity', NULL),
    (3, 'temperature', '2022-04-01T00:00:00Z'),
    (4, 'pressure', '2023-05-15T12:30:00Z'),
```

## Kafka 

**subscribe to kafka topic**
```bash
## Set topic
docker exec -it kafka kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic sensorvalues

## List topics
docker exec -it kafka kafka-topics --list --bootstrap-server kafka:9092

## Produce
docker exec -it kafka kafka-console-producer --topic message_topic --bootstrap-server localhost:9092

## Consume
docker exec -it kafka kafka-console-consumer --topic message_topic --bootstrap-server localhost:9092 --from-beginning
```

## Opensearch

**create elastic index**
```bash
docker exec -it opensearch curl -X PUT "localhost:9200/myindex" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  }
}
'
```
**add a sample document**
```bash
docker exec -it opensearch curl -X POST "localhost:9200/myindex/_doc/1" -H 'Content-Type: application/json' -d'
{
  "id": 1,
  "long": 4.895168,
  "lat": 52.370216,
  "humidity": 0.4,
  "temperature": 23,
  "timestamp": "2025-06-14T12:00:00Z"
}
'
```
**check document indexed correctly**
```bash
docker exec -it opensearch curl -X GET "localhost:9200/myindex/_doc/1"
```

**delete a document**
```bash
docker exec -it opensearch curl -X DELETE "localhost:9200/myindex/_doc/1"
```

**search the index**
```bash
docker exec -it opensearch curl -X GET "localhost:9200/myindex/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_all": {}
  }
}
'
```

## Publishers
Kafka-confluent and Opensearch with python

**pub/main.py**
pip install flastapi confluent-kafka opensearch

```python
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
```

And the `Dockerfile.pub.broker`

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*
RUN pip install confluent-kafka fastapi uvicorn pydantic requests
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x wait-for-kafka.sh
CMD ["./wait-for-kafka.sh"]
```
with shell script `wait-for-kafka.sh`

```bash
#!/bin/sh
echo "⏳ Waiting for Kafka at $KAFKA_BOOTSTRAP_SERVERS..."
until nc -z kafka 29092; do
  sleep 15
done
echo "✅ Kafka is up - starting app"
exec uvicorn main:app --host 0.0.0.0 --port 8000
```

Now add this to the previous docker-compose.yml:
```Dockerfile
  pub-kafka:
    build:
      context: ./pub
      dockerfile: Dockerfile.pub.broker
    container_name: pub-kafka
    ports:
      - "8100:8000"
    depends_on:
      - kafka
      - postgres
      - opensearch
    env_file:
      - .env
```
Then, to update do (note that -v does delete the volume, and thus the topics and indexes already set):

```
docker compose down -v
docker compose --env-file .env up --build
```

Now check if this works:

```bash
curl -X POST "http://localhost:8100/produce?message=HelloKafka"
```
This should produce: 
```
{"status":"sent","message":"HelloKafka"} 
```

**stream-data.py**
pip install pydantic requests numpy
```python
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
        value = max(-40.0, min(100.0, value))

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

def stream(event_coun):
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
    stream(10000)
```

Now, make sure venv is enabled (python3 -m venv venv, source venv/bin/activate pip install .. ) and run 

```bash
python stream-data.py
```

this will look like:

  [OpenSearch] Indexed doc: 2-802
  [Kafka] Sent temperature event: {"id":"4","value":22.995006348036892,"timestamp":"2025-06-14T23:47:17Z"}
  [Kafka] Sent humidity event: {"id":"4","value":63.76472341161971,"timestamp":"2025-06-14T23:47:17Z"}
  [OpenSearch] Indexed doc: 4-803
  [Kafka] Sent temperature event: {"id":"3","value":25.82034944019731,"timestamp":"2025-06-14T23:47:17Z"}
  [Kafka] Sent humidity event: {"id":"3","value":45.16394527383489,"timestamp":"2025-06-14T23:47:17Z"}

## Consumers
**sub/main.py**
pip install flastapi confluent-kafka opensearch psycopg2
```python
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
```

And the `Dockerfile.sub.broker`

```Dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    curl \
    wget \
    gnupg \
    librdkafka-dev \
    && apt-get clean
RUN pip install --no-cache-dir \
    confluent-kafka \
    fastapi \
    uvicorn \
    pydantic \
    requests \
    psycopg2-binary \
    geopy
WORKDIR /app
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

Now add this again to the previous docker-compose.yml:
```Dockerfile
  sub-kafka:
    build:
      context: ./sub
      dockerfile: Dockerfile.sub.broker
    container_name: sub-kafka
    ports:
      - "8101:8001"
    depends_on:
      - kafka
      - postgres
      - opensearch
    env_file:
      - .env
```

Then, to update do (note that -v does delete the volume, and thus the topics and indexes already set):

```
docker compose down -v
docker compose --env-file .env up --build
```

Now check if this works:

```bash
curl "http://localhost:8101/consume"
curl "http://localhost:8101/actions"
```