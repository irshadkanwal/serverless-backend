---
created: 2025-09-22T18:29:15Z
last_updated: 2025-09-22T18:29:15Z
version: 1.0
author: Claude Code PM System
---

# Project Overview

## System Architecture

### High-Level Architecture
```
Client Apps → API Gateway → FastAPI Backend → Agent System → Storage Layer
                                   ↓
                          Azure OpenAI Service
```

### Component Overview
1. **API Layer**: FastAPI-based REST endpoints
2. **Agent System**: Multi-agent orchestration for coaching
3. **State Machine**: FSM managing conversation flow
4. **Storage Layer**: PostgreSQL with vector and graph extensions
5. **External Services**: Azure OpenAI for LLM capabilities

## Feature Inventory

### Core Features

#### Conversation Management
- **State-Aware Dialogues**: FSM-driven conversation flow
- **Context Preservation**: Session memory across interactions
- **Dynamic Responses**: Adaptive to user needs and emotions
- **Professional Standards**: Coaching best practices embedded

#### Agent Capabilities
- **Coaching Agent**: Primary conversation orchestrator
- **Moderation Agent**: Content safety and appropriateness
- **Context Analyzer**: Understanding user situation
- **Content Analyzer**: Topic depth and relevance
- **Emotion Analyzer**: Emotional state detection
- **Stage Transition Analyzer**: Optimal flow decisions
- **Session Summary Agent**: Key takeaways generation
- **Stage Summary Agent**: Phase-specific insights

#### API Endpoints
- `POST /chat`: Main conversation endpoint
- `GET /session/{id}`: Retrieve session details
- `POST /session/summary`: Generate session summary
- `GET /health`: System health check
- `GET /docs`: Interactive API documentation

#### Data Management
- Session persistence in PostgreSQL
- Vector embeddings for similarity search
- Graph relationships for context mapping
- Memory system for long-term recall

### Supporting Features

#### Security & Compliance
- Rate limiting per endpoint
- Content Security Policy (CSP) headers
- Input validation and sanitization
- Secure configuration management
- Audit logging capabilities

#### Development Tools
- Automated testing with pytest
- Code quality with Ruff
- Pre-commit hooks for consistency
- Docker containerization
- CI/CD pipeline automation

#### Monitoring & Observability
- Structured logging throughout
- Error tracking and reporting
- Performance metrics collection
- Health check endpoints
- Deployment status tracking

## Integration Capabilities

### Current Integrations
- **Azure OpenAI**: GPT-4 and other models
- **PostgreSQL**: Primary data storage
- **pgvector**: Vector similarity search
- **Apache AGE**: Graph database capabilities
- **Neo4j**: Advanced graph operations
- **LightRAG**: Graph-based retrieval
- **mem0ai**: Memory management

### API Integration
- RESTful API design
- JSON request/response format
- Swagger/OpenAPI documentation
- CORS configuration support
- Rate limiting controls

### Deployment Integration
- GitHub Actions CI/CD
- Docker container support
- Environment-based configuration
- Serverless deployment ready
- Auto-scaling capabilities

## System Capabilities

### Performance Characteristics
- Async/await for non-blocking operations
- Connection pooling for database efficiency
- Caching strategies for common queries
- Optimized prompt engineering
- Batch processing support

### Scalability Features
- Stateless service design
- Horizontal scaling support
- Database connection management
- Queue-based processing (planned)
- Load balancing ready

### Reliability Features
- Error recovery mechanisms
- Fallback strategies for failures
- Transaction rollback support
- Retry logic with backoff
- Circuit breaker patterns

## Configuration Management

### Environment Configuration
- `.env` file for local development
- Environment variables for production
- Separate configs per environment
- Secure secrets management
- Feature flag support

### Application Settings
- Pydantic settings validation
- Type-safe configuration
- Default value handling
- Configuration documentation
- Runtime configuration updates

## Development Workflow

### Local Development
```bash
# Setup
uv sync
source .venv/bin/activate

# Run
uv run fastapi dev app/main.py

# Test
uv run pytest

# Lint
uv run ruff check
```

### Deployment Pipeline
1. Push to main → Dev deployment
2. Create PR → Run tests
3. Merge PR → Update dev
4. Create release → Deploy to production

## API Usage Examples

### Starting a Conversation
```json
POST /chat
{
  "session_id": "uuid",
  "message": "I'd like to discuss my career goals",
  "context": {}
}
```

### Response Format
```json
{
  "response": "I'd be happy to explore your career goals with you...",
  "stage": "exploration",
  "metadata": {
    "confidence": 0.95,
    "emotion": "engaged"
  }
}
```

## System Requirements

### Runtime Requirements
- Python 3.12+
- PostgreSQL 16+
- 2GB+ RAM
- Internet connectivity

### Development Requirements
- uv package manager
- Git version control
- Docker (optional)
- VS Code or PyCharm

## Current Limitations

### Technical Limitations
- Single language (English only)
- Text-only interaction
- Session length constraints
- API rate limits

### Functional Limitations
- No voice/video support
- Limited multi-session continuity
- Basic analytics only
- Manual intervention not supported

## Roadmap Highlights

### Near-term (Q4 2024)
- Enhanced memory system
- Improved context retrieval
- Advanced analytics dashboard
- Performance optimizations

### Mid-term (Q1-Q2 2025)
- Multi-language support
- Voice interaction capability
- Advanced reporting
- Team coaching features

### Long-term (2025+)
- Video coaching support
- AI coach personality customization
- Integration marketplace
- White-label solutions