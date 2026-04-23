FROM mirror.gcr.io/library/python:3.12-slim

# Install git for git dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Copy the application into the container.
COPY . /app

WORKDIR /app

# Install dependencies without the project itself
RUN uv sync --frozen --no-cache

CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
