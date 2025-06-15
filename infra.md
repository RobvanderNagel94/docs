---
layout: default
title: Microservice
---

## Examples

Design a microservice that runs every eg. *hour* to identify sensors needing maintenance actions. It outputs a list of sensors and their maintenance trigger and timestamp. It only consumes messages between [last_run_time, current_time) based on these rules:

- **Rule A**: Sensor humidity exceeds when relative humidity level > 90%.

- **Rule B**: Sensor temperature exceeds when temperature > 40 Degrees Celsius.

The service outputs sensor IDs requiring maintenance along with the triggering rule (A or B).


### Method
For a set of sensors indexed by $i = 1, 2, 3, 4$. Each sensor has a type (e.g. temperature, vibration, humidity, IR) and logs data. Additionally, each sensor is equiped with other sensory to track status indicators of the sensor, ie. lon, lat, humid and temp.

Let the output of each sensor $i$ at time $t$ be represented as:

$$
\text{Sensor}_i(t) = ( \text{id}_i, \text{type}_i, \text{value}_i(t), \text{lon}_i(t), \text{lat}_i(t), \text{humid}_i(t), \text{temp}_i(t), \text{ts}_i(t) )
$$

where:
- $\text{id}_i$ is the unique identifier
- $\text{type}_i$ is the sensor type ["temperature", "vibration", "humidity", "IR"]
- $\text{value}_i(t)$ is the sensor reading at time $t$
- $\text{lon}_i(t)$ is the longitudinal coordinate at time $t$
- $\text{lat}_i(t)$ is the latitudinal coordinate at time $t$
- $\text{humid}_i(t)$ is the humidity level at time $t$
- $\text{temp}_i(t)$ is the temperature level at time $t$
- $\text{ts}_i(t)$ is the time of the reading.

For each sensor three steps are done. Metadata *id, type, unit* and *last_maintenance_date* are saved in **postgres**. Sensor values *id, value, ts* are saved to **kafka**. Internal sensor values are stored in **opensearch**, eg, *id, lon, lat, humid, temp, ts*.

**Example static Postgres**

```
id, type, unit, last_maintenance_date
(1, 'vibration', 'mm/s' ,'2023-01-01T00:00:00Z'),
(2, 'vibration', 'mm/s,  NULL),
(3, 'pressure', 'mbar', '2022-04-01T00:00:00Z'),
(4, 'vibration', 'mm/s, '2023-05-15T12:30:00Z'),
```

**Example stream to Kafka**
```
{"id": 1, "value": 0.123, "ts": "2025-01-01T00:00:00Z"}
```
to a kafka broker on topic name `"rawsensorvalues"`.

**Example stream to Opensearch**
```
{"id": 1, "lon": 4.895168, "lat": 52.370216, "humid": 82.5, "temp": 20.0, "ts": "2025-01-01T00:00:00Z"}
```

to a opensearch broker on name `"sensorindex"`.

Note that there are three DB involved: 
- **postgres** (meta sensor)
- **kafka** (raw sensor values)
- **opensearch** (internal sensor values) 

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
    unit VARCHAR(50) NOT NULL,
    last_maintenance_date TIMESTAMP NULL
);

INSERT INTO sensors (id, type, unit, last_maintenance_date) VALUES
    (1, 'vibration', 'mm/s' ,'2023-01-01T00:00:00Z'),
    (2, 'vibration', 'mm/s',  NULL),
    (3, 'pressure',  'mbar', '2022-04-01T00:00:00Z'),
    (4, 'vibration', 'mm/s', '2023-05-15T12:30:00Z');
```

## Kafka 

**subscribe to kafka topic**
```bash
## Set topic
docker exec -it kafka kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic rawsensorvalues

## List topics
docker exec -it kafka kafka-topics --list --bootstrap-server kafka:9092

## Produce
docker exec -it kafka kafka-console-producer --topic rawsensorvalues --bootstrap-server localhost:9092

## Consume
docker exec -it kafka kafka-console-consumer --topic rawsensorvalues --bootstrap-server localhost:9092 --from-beginning
```

## Opensearch

**create elastic index**
```bash
docker exec -it opensearch curl -X PUT "localhost:9200/sensorindex" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  }
}
'
```
**add a document**
```bash
docker exec -it opensearch curl -X POST "localhost:9200/sensorindex/_doc/1" -H 'Content-Type: application/json' -d'
{
  "id": 1,
  "lon": 4.895168,
  "lat": 52.370216,
  "humid": 0.4,
  "temp": 23,
  "ts": "2025-06-14T12:00:00Z"
}
'
```
**check document indexed correctly**
```bash
docker exec -it opensearch curl -X GET "localhost:9200/sensorindex/_doc/1"
```

**delete a document**
```bash
docker exec -it opensearch curl -X DELETE "localhost:9200/sensorindex/_doc/1"
```

**search the index**
```bash
docker exec -it opensearch curl -X GET "localhost:9200/sensorindex/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_all": {}
  }
}
'
```

## Publishers
Kafka-confluent and Opensearch with python

**pub/kafka-broker.py**
pip install flastapi confluent-kafka opensearch pydantic

```python
ffrom fastapi import FastAPI, HTTPException
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
    try:
        producer.produce(KAFKA_TOPIC, key=event.id, value=event.json())
        producer.flush()
        return {"status": "sent", "message": event.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-topic")
def create_kafka_topic(request: TopicRequest):
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
```

**pub/opensearch-broker.py** pip install requests fastapi opensearch pydantic

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

OPENSEARCH_URL = "http://opensearch:9200"
INDEX_NAME = "sensorindex"

app = FastAPI()

class SensorDocument(BaseModel):
    id: int
    lon: float
    lat: float
    humid: float
    temp: float
    ts: str

@app.put("/create-index")
def create_index():
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}"
    body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    }
    r = requests.put(url, json=body)
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"status": "created", "response": r.json()}

@app.post("/add-doc")
def add_document(doc: SensorDocument):
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_doc/{doc.id}"
    r = requests.post(url, json=doc.dict())
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"status": "indexed", "response": r.json()}

@app.get("/get-doc/{doc_id}")
def get_document(doc_id: int):
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_doc/{doc_id}"
    r = requests.get(url)
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Document not found")
    return r.json()

@app.delete("/delete-doc/{doc_id}")
def delete_document(doc_id: int):
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_doc/{doc_id}"
    r = requests.delete(url)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"status": "deleted", "response": r.json()}

@app.get("/search")
def search_all():
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_search"
    r = requests.get(url, json={"query": {"match_all": {}}})
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()
```


And the `Dockerfile.kafka` and `Dockerfile.opensearch`, respectively

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
```Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*
RUN pip install fastapi uvicorn pydantic requests opensearch
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "opensearch-broker:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

with shell script `wait-for-kafka.sh`

```bash
#!/bin/sh
echo "Waiting for Kafka at $KAFKA_BOOTSTRAP_SERVERS..."
until nc -z kafka 29092; do
  sleep 15
done
echo "✅ Kafka is up - starting app"
exec uvicorn main:app --host 0.0.0.0 --port 8000
```

Now add this to the previous docker-compose.yml:
```Dockerfile
  api-pub-kafka:
    build:
      context: ./pub
      dockerfile: Dockerfile.kafka
    container_name: api-pub-kafka
    ports:
      - "8100:8000"
    depends_on:
      - kafka
      - postgres
      - opensearch
    env_file:
      - .env

  api-pub-opensearch:
    build:
      context: ./pub
      dockerfile: Dockerfile.opensearch
    container_name: api-pub-opensearch
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
curl -X POST http://localhost:8100/create-topic \
  -H "Content-Type: application/json" \
  -d '{"topic": "rawsensorvalues"}'

curl -X POST http://localhost:8100/produce \
  -H "Content-Type: application/json" \
  -d '{
    "id": "1",
    "value": 0.532,
    "ts": "2025-06-15T10:00:00Z"
}'

curl -X PUT http://localhost:8101/create-index

curl -X POST http://localhost:8101/add-doc \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "lon": 4.895168,
    "lat": 52.370216,
    "humid": 50.0,
    "temp": 20.0,
    "ts": "2025-06-15T10:00:00Z"
}'

curl http://localhost:8101/search
```

**pub/stream-data.py**
pip install pydantic requests numpy
```python
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
    3: {"value": 29.454, "temp": 22.0, "humid": 45.0, "lat": 34.052235, "lon": -33.243683, "ts": "2025-01-01T00:00:00Z"},
    4: {"value": 0.906, "temp": 19.0, "humid": 60.0, "lat": 37.774929, "lon": -122.419416, "ts": "2025-01-01T00:00:00Z"},
}

init_boundaries = {
    1: {"value": (-1, 1), "temp": (0, 50), "humid": (0, 100), "lat": (52.36, 52.38), "lon": (4.89, 4.91)},
    2: {"value": (-1, 1), "temp": (0, 50), "humid": (0, 100), "lat": (40.70, 40.73), "lon": (-74.01, -74.00)},
    3: {"value": (-50, 50), "temp": (0, 50), "humid": (0, 100), "lat": (34.05, 34.06), "lon": (-33.25, -33.24)},
    4: {"value": (-1, 1), "temp": (0, 50), "humid": (0, 100), "lat": (37.77, 37.78), "lon": (-122.42, -122.41)},
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
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Generate values within boundaries
        value = random_value(sensor_id, "value")
        temp = random_value(sensor_id, "temp")
        humid = random_value(sensor_id, "humid")
        lat = random_value(sensor_id, "lat")
        lon = random_value(sensor_id, "lon")

        # Send Kafka event (primary sensor measurement only)
        kafka_event = KafkaEvent(id=str(sensor_id), value=value, ts=timestamp)
        try:
            resp = requests.post(KAFKA_PRODUCE_URL, json=kafka_event.dict())
            resp.raise_for_status()
            print(f"[Kafka] Sent value={value:.3f} | id={sensor_id}, ts={timestamp}")
        except Exception as e:
            print(f"[Kafka] Error: {e}")

        # Send OpenSearch document (sensor internal state)
        os_doc = OpensearchDocument(id=str(sensor_id), lon=lon, lat=lat, humid=humid, temp=temp, ts=timestamp)
        try:
            resp = requests.post(OPENSEARCH_ADD_INDEX_URL, json=os_doc.dict())
            resp.raise_for_status()
            print(f"[OpenSearch] Indexed id={sensor_id}, ts={timestamp}, lon={lon}, lat={lat}, humid={humid}, temp={temp}")
        except Exception as e:
            print(f"[OpenSearch] Error: {e}")

        time.sleep(delay)

if __name__ == "__main__":
    create_topic()
    create_index()
    # Start streaming data
    stream(event_count=10000, delay=0.0)
```

Now, make sure venv is enabled (python3 -m venv venv, source venv/bin/activate pip install .. ) and run 

```bash
python stream-data.py
```

this will look like:

[Kafka] Sent value=43.664 | id=3, ts=2025-06-15T15:52:20Z
[OpenSearch] Indexed id=3, ts=2025-06-15T15:52:20Z, lon=-33.243837, lat=34.054073, humid=40.910258, temp=21.32264
[Kafka] Sent value=-47.677 | id=3, ts=2025-06-15T15:52:20Z
[OpenSearch] Indexed id=3, ts=2025-06-15T15:52:20Z, lon=-33.242361, lat=34.056848, humid=17.489111, temp=44.032833
[Kafka] Sent value=0.694 | id=3, ts=2025-06-15T15:52:20Z
[OpenSearch] Indexed id=3, ts=2025-06-15T15:52:20Z, lon=-33.244146, lat=34.054948, humid=78.588193, temp=38.279888

## Consumers (microservice)
**sub/main.py**
pip install fastapi confluent-kafka opensearch psycopg2 requests
```python
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
                            "timestamp": {
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

    if sensor_type in ['vibration', 'pressure']:
        for doc in history:
            humidity = doc.get('humid')
            temperature = doc.get('temperature')

            if humidity is not None and humidity > 80:
                triggered.append({
                    "id": sensor_id,
                    "rule": "High humidity > 80",
                    "unit": unit,
                    "type": doc.get('type', sensor_type),
                    "lat": doc.get('lat'),
                    "lon": doc.get('lon'),
                    "last_maintenance_date": last_maintenance_date,
                    "ts": doc.get('timestamp')
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
                    "ts": doc.get('timestamp')
                })
                break

    return triggered


def guard_maintenance_policy(message_value: str, from_time, to_time):
    try:
        data = json.loads(message_value)
        sensor_id = int(data.get("id"))
        timestamp = data.get("timestamp")

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
```

And the `Dockerfile.microservice`

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
    opensearch \
    fastapi \
    uvicorn \
    pydantic \
    requests \
    psycopg2-binary \
WORKDIR /app
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
```

Now add this again to the previous docker-compose.yml:
```Dockerfile
  microservice:
    build:
      context: ./sub
      dockerfile: Dockerfile.microservice
    container_name: microservice
    ports:
      - "8102:8002"
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