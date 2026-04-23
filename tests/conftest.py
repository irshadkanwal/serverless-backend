import os

# Set environment variables at import time before any app modules load
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "test")
os.environ.setdefault("NEO4J_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_MEMORY_DATABASE", "test")
os.environ.setdefault("AZURE_API_ENDPOINT", "https://test.openai.azure.com")
os.environ.setdefault("AZURE_API_KEY", "test-key")
os.environ.setdefault("AZURE_API_VERSION", "2024-02-01")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
