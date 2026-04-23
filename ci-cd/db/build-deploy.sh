#!/bin/bash

set -e
  
git pull

docker build -f Dockerfile.db_pgvectore_age -t postgres-db-pgvector-age:local .

# docker compose down
docker compose up -d --force-recreate

docker system prune -af
