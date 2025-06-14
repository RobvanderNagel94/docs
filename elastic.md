---
layout: default
title: Elastic
---

## Commands
### Find docs where a field contains a value
```bash
{
  "query": {
    "match": {
      "title": "elasticsearch"
    }
  }
}
```

### Term Filter (exact match)
```bash
{
  "query": {
    "term": {
      "status": "active"
    }
  }
}
```

### Range Filter
```bash
{
  "query": {
    "range": {
      "price": {
        "gte": 10,
        "lte": 50
      }
    }
  }
}
```

### Time Range Filter
```bash
{
  "query": {
    "range": {
      "timestamp": {
        "gte": "now-7d/d",
        "lte": "now/d"
      }
    }
  }
}
```

### Sort & Pagination
```bash
{
  "query": {
    "match_all": {}
  },
  "sort": [
    {
      "date": "desc"
    }
  ],
  "from": 0,
  "size": 10
}
```

### Boolean Logic
```bash
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "title": "search"
          }
        }
      ],
      "filter": [
        {
          "term": {
            "status": "active"
          }
        }
      ],
      "must_not": [
        {
          "term": {
            "type": "deprecated"
          }
        }
      ]
    }
  }
}
```

### Multi-Match (search multiple fields)
```bash
{
  "query": {
    "multi_match": {
      "query": "fast text",
      "fields": ["title", "description"]
    }
  }
}
```

### Fuzzy match
```bash
{
  "query": {
    "match": {
      "name": {
        "query": "elastcsearch",
        "fuzziness": "AUTO"
      }
    }
  }
}
```

### Aggregations; Count by category
```bash
{
  "size": 0,
  "aggs": {
    "by_category": {
      "terms": {
        "field": "category.keyword"
      }
    }
  }
}
```

### Average value
```bash
{
  "size": 0,
  "aggs": {
    "avg_price": {
      "avg": {
        "field": "price"
      }
    }
  }
}
```

### Search via cURL
```bash
curl -X POST "localhost:9200/my-index/_search" -H "Content-Type: application/json" -d '{
  "query": {
    "match": {
      "title": "elasticsearch"
    }
  }
}'
```

### Update by query
```bash
curl -X POST "localhost:9200/index/_update_by_query" -H "Content-Type: application/json" -d '{
  "script": {
    "source": "ctx._source.active = false"
  },
  "query": {
    "term": {
      "status": "inactive"
    }
  }
}'
```

## Example setup

```bash
# 1. Test if Elasticsearch is running and reachable
curl -X GET "localhost:9200/"

# Expected output: JSON with cluster name, version, and status info

# 2. Create an index called "my-index" with basic settings and mappings
curl -X PUT "localhost:9200/my-index" -H "Content-Type: application/json" -d '{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "title": { "type": "text" },
      "price": { "type": "float" },
      "timestamp": { "type": "date" }
    }
  }
}'

# 3. Index (insert) a document into "my-index"
curl -X POST "localhost:9200/my-index/_doc/1" -H "Content-Type: application/json" -d '{
  "title": "Test document",
  "price": 19.99,
  "timestamp": "2025-06-14T12:00:00Z"
}'

# 4. Retrieve the document by ID
curl -X GET "localhost:9200/my-index/_doc/1"

# 5. Search all documents in the index (simple match_all query)
curl -X GET "localhost:9200/my-index/_search" -H "Content-Type: application/json" -d '{
  "query": {
    "match_all": {}
  }
}'
```

## Python API
pip install elasticsearch
```python
from datetime import datetime
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

if es.ping():
    print("Elasticsearch is up!")
else:
    print("Failed to connect")

index_name = "my-index"
if not es.indices.exists(index=index_name):
    es.indices.create(
        index=index_name,
        body={
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "price": {"type": "float"},
                    "timestamp": {"type": "date"}
                }
            }
        }
    )
    print(f"Index '{index_name}' created")
else:
    print(f"Index '{index_name}' already exists")

# Index a document
doc = {
    "title": "Test document",
    "price": 19.99,
    "timestamp": datetime.utcnow()
}
res = es.index(index=index_name, id=1, document=doc)
print("Document indexed:", res['result'])

# Get document by ID
doc_get = es.get(index=index_name, id=1)
print("Retrieved document:", doc_get['_source'])

# Search all documents with match_all query
search_res = es.search(
    index=index_name,
    body={"query": {"match_all": {}}}
)

print(f"Found {search_res['hits']['total']['value']} documents")
for hit in search_res['hits']['hits']:
    print(hit["_source"])
```