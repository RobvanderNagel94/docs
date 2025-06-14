---
layout: default
title: Elastic
---

## Commands
```bash
# Find docs where a field contains a value
{
  "query": {
    "match": {
      "title": "elasticsearch"
    }
  }
}

# Term Filter (exact match)
{
  "query": {
    "term": {
      "status": "active"
    }
  }
}

# Range Filter
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

# Time Range Filter
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

# Sort & Pagination
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

# Boolean Logic
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

# Multi-Match (search multiple fields)
{
  "query": {
    "multi_match": {
      "query": "fast text",
      "fields": ["title", "description"]
    }
  }
}

# Fuzzy match
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

# Aggregations; Count by category
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

# Average value
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

# Search via cURL
curl -X POST "localhost:9200/my-index/_search" -H "Content-Type: application/json" -d '{
  "query": {
    "match": {
      "title": "elasticsearch"
    }
  }
}'

# Update by query
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