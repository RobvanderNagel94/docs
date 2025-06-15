from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

OPENSEARCH_URL = "http://opensearch:9200"
INDEX_NAME = "sensorindex"

class SensorDocument(BaseModel):
    id: int
    lon: float
    lat: float
    humid: float
    temp: float
    ts: str

@app.put("/create-index")
def create_index():
    """Create an OpenSearch index."""
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
    """Add a document to OpenSearch."""
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_doc/{doc.id}"
    r = requests.post(url, json=doc.dict())
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"status": "indexed", "response": r.json()}

@app.get("/get-doc/{doc_id}")
def get_document(doc_id: int):
    """Retrieve a document by ID."""
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_doc/{doc_id}"
    r = requests.get(url)
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Document not found")
    return r.json()

@app.delete("/delete-doc/{doc_id}")
def delete_document(doc_id: int):
    """Delete a document by ID."""
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_doc/{doc_id}"
    r = requests.delete(url)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"status": "deleted", "response": r.json()}

@app.get("/search")
def search_all():
    """Search all documents in the index."""
    url = f"{OPENSEARCH_URL}/{INDEX_NAME}/_search"
    r = requests.get(url, json={"query": {"match_all": {}}})
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()
