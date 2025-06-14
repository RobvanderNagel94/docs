---
layout: default
title: Docker
---
```bash
docker ps                     # List running containers
docker ps -a                  # List all containers (running and stopped)
docker run <image>            # Run a container from an image
docker stop <container_id>    # Stop a running container
docker start <container_id>   # Start a stopped container
docker restart <container_id> # Restart a running or stopped container
docker exec -it <container_id> <command>  # Execute a command inside a running container
docker rm <container_id>      # Remove a stopped container
docker logs <container_id>    # Show logs of a container
docker attach <container_id>  # Attach to a running container's process
docker images                 # List all Docker images
docker pull <image>           # Pull an image from Docker Hub
docker build <path>           # Build an image from a Dockerfile at <path>
docker rmi <image>            # Remove a Docker image
docker tag <image> <new_tag>  # Tag an image with a new name
docker push <image>           # Push an image to a Docker registry (e.g., Docker Hub)
docker save -o <filename> <image>   # Save an image to a tarball
docker load -i <filename>         # Load an image from a tarball
docker volume ls              # List all Docker volumes
docker volume inspect <volume_name> # Inspect a specific Docker volume
docker volume create <volume_name> # Create a new volume
docker volume rm <volume_name> # Remove a Docker volume
docker network ls             # List all Docker networks
docker network create <network_name>  # Create a new Docker network
docker network inspect <network_name>  # Inspect a specific Docker network
docker network rm <network_name>  # Remove a Docker network
docker system df              # Show disk usage by Docker objects (containers, images, volumes)
docker system prune           # Remove all unused containers, networks, images (and volumes)
docker system prune -a        # Remove all unused containers, networks, images, and volumes
docker volume prune           # Remove all unused volumes
docker network prune          # Remove all unused networks
docker info                  # Show Docker system-wide information
docker version               # Show Docker version information
docker info --format '{{.ID}}' # Show only Docker ID
docker inspect <container_id> # Show detailed information about a specific container
docker inspect <image>        # Show detailed information about an image
docker login                 # Login to Docker Hub or other Docker registry
docker logout                # Logout from Docker Hub or other Docker registry
docker search <term>         # Search for images in the Docker registry
docker container prune        # Remove all stopped containers
docker image prune            # Remove unused images (not referenced by containers)
docker volume prune           # Remove unused volumes
docker network prune          # Remove unused networks
docker-compose config        # Validate the syntax of a docker-compose.yml file
docker-compose push          # Push services defined in the docker-compose.yml to a registry
docker-compose up             # Start services defined in docker-compose.yml
docker-compose down           # Stop and remove containers defined in docker-compose.yml
docker-compose build          # Build or rebuild services defined in docker-compose.yml
docker-compose logs           # Show logs of all services in docker-compose
docker-compose exec <service> <command> # Execute a command in a running service container
docker-compose ps             # List running containers managed by Docker Compose
```

## Examples

docker-compose.yml file
```yml
services:

  zookeeper:
    image: bitnami/zookeeper:latest
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ALLOW_ANONYMOUS_LOGIN: yes

  kafka:
    image: confluentinc/cp-kafka:7.4.0
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
  
  pub:
    build:
      context: ./pub
      dockerfile: Dockerfile.p.example
    container_name: pub
    ports:
      - "8000:8000"
    depends_on:
      - kafka
    
  sub:
    build:
      context: ./sub
      dockerfile: Dockerfile.s.example
    container_name: sub
    ports:
      - "8001:8001"
    depends_on:
      - kafka
```

with `Dockerfile.p.example`

```Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn","main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```