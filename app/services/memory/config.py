import os
import urllib.parse


class MemoryConfig:
    def __init__(self):
        self.config = {
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": os.environ["NEO4J_URI"],
                    "username": os.environ["NEO4J_USER"],
                    "password": os.environ["NEO4J_PASSWORD"],
                },
                "custom_prompt": (
                    "When creating relationships, replace hyphens with underscores."
                ),
            },
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "host": os.environ["POSTGRES_HOST"],
                    "port": int(os.environ["POSTGRES_PORT"]),
                    "user": os.environ["POSTGRES_USER"],
                    "password": urllib.parse.quote_plus(
                        os.environ["POSTGRES_PASSWORD"]
                    ),
                    "dbname": os.environ["POSTGRES_MEMORY_DATABASE"],
                    "collection_name": "mem0",
                    "embedding_model_dims": 3072,
                    "diskann": True,
                },
            },
            "embedder": {
                "provider": "azure_openai",
                "config": {
                    "model": "text-embedding-3-large",
                    "azure_kwargs": {
                        "api_version": "2024-02-01",
                        "azure_deployment": "text-embedding-3-large",
                        "azure_endpoint": os.environ["AZURE_API_ENDPOINT"],
                        "api_key": os.environ["AZURE_API_KEY"],
                    },
                },
            },
            "llm": {
                "provider": "azure_openai",
                "config": {
                    "model": "gpt-4.1",
                    "temperature": 0.1,
                    "max_tokens": 2000,
                    "azure_kwargs": {
                        "azure_deployment": "gpt-4.1",
                        "api_version": os.environ["AZURE_API_VERSION"],
                        "azure_endpoint": os.environ["AZURE_API_ENDPOINT"],
                        "api_key": os.environ["AZURE_API_KEY"],
                    },
                },
            },
        }

    @property
    def memory_search_tools(self):
        return [
            {
                "type": "function",
                "name": "searchMemory",
                "description": (
                    "Search the user's conversation history, memories, and personal "
                    "information. Use this to: 1) Get context when they reference "
                    "past events, preferences, or goals, 2) Find previous answers "
                    "to avoid repeating questions, 3) Build on past discussions. "
                    "Always search before asking questions that might have been "
                    "covered before."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Search query for relevant conversation history or "
                                "user information. Use keywords from their current "
                                "message, past topics discussed, or questions you're "
                                "considering asking."
                            ),
                        }
                    },
                    "required": ["query"],
                },
            }
        ]
