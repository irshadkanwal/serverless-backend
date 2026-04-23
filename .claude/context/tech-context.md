---
created: 2025-09-22T18:29:15Z
last_updated: 2025-09-22T18:29:15Z
version: 1.0
author: Claude Code PM System
---

# Technical Context

## Core Technology Stack
- **Language**: Python 3.12+
- **Framework**: FastAPI (with standard extensions)
- **Package Manager**: uv (modern Python package management)
- **Database**: PostgreSQL 16 with pgvector and AGE extensions
- **Deployment**: Serverless architecture

## Key Dependencies

### Web Framework & API
- `fastapi[standard]` - Modern async web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation using Python type annotations
- `pydantic_settings` - Settings management
- `slowapi` - Rate limiting for FastAPI

### AI & ML Components
- `openai` - OpenAI API integration
- `azure-identity` (>=1.25.0) - Azure authentication
- `lightrag-hku` - Graph-based RAG implementation (custom fork)
- `mem0ai` - Memory management system
- `rank-bm25` (>=0.2.2) - BM25 ranking algorithm

### Database & Storage
- `asyncpg` - Async PostgreSQL driver
- `psycopg2-binary` - PostgreSQL adapter
- `neo4j` - Neo4j graph database client
- `langchain-neo4j` - LangChain Neo4j integration

### Async & Networking
- `asyncio` (4.0.0) - Asynchronous I/O
- `aiohttp` (3.12.15) - Async HTTP client/server
- `backoff` - Retry logic with exponential backoff

### Development Tools
- `pytest` (>=7.0) - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage
- `ruff` - Fast Python linter and formatter
- `pre-commit` - Git hook framework

## Development Environment
- **Virtual Environment**: Managed by uv
- **Python Version**: 3.12+ required
- **IDE Support**: VS Code, PyCharm compatible
- **OS Support**: macOS, Linux, Windows (WSL recommended)

## Build System
- **Build Backend**: Hatchling
- **Package Format**: Wheel distribution
- **Direct References**: Enabled for Git dependencies

## Quality Assurance

### Linting Configuration (Ruff)
- Line length: 88 characters
- Target version: Python 3.12
- Extended rules for:
  - Code quality (F, W, E)
  - Import sorting (I)
  - Modern Python features (UP)
  - Performance (PERF)
  - Argument usage (ARG)
  - Simplification (SIM)

### Testing Configuration
- Async mode: Auto
- Default fixture scope: Function
- Coverage reporting enabled

## External Services
- **Azure OpenAI**: Primary LLM provider
- **PostgreSQL**: Main database with vector support
- **Neo4j**: Graph database for relationships
- **GitHub Actions**: CI/CD pipeline

## API Configuration
- **Azure API Version**: 2025-03-01-preview
- **FastAPI Features**: Auto-documentation (Swagger/ReDoc)
- **Security**: CSP headers, rate limiting
- **CORS**: Configurable per environment

## Deployment Infrastructure
- **Development**: Auto-deploy on main branch push
- **Production**: Release-triggered deployments
- **Containerization**: Docker support
- **Orchestration**: docker-compose for local development

## Version Control
- **VCS**: Git
- **Platform**: GitHub
- **Workflow**: Trunk-based development
- **Branching**: Short-lived feature branches

## Performance Considerations
- Async/await throughout for non-blocking I/O
- Connection pooling for database access
- Rate limiting to prevent abuse
- Vector indexing for similarity search
- Graph database for relationship queries