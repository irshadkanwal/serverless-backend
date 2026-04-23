---
created: 2025-09-22T18:29:15Z
last_updated: 2025-09-22T18:29:15Z
version: 1.0
author: Claude Code PM System
---

# System Patterns

## Architectural Style
- **Pattern**: Agent-Based Architecture
- **Communication**: Asynchronous message passing
- **State Management**: Finite State Machine (FSM)
- **API Design**: RESTful with FastAPI
- **Data Flow**: Request → Middleware → Routes → Services → Agents → Storage

## Core Design Patterns

### 1. Agent Pattern
- Specialized agents for distinct responsibilities
- Base agent interface for consistency
- Composition over inheritance
- Each agent handles specific domain logic:
  - `CoachingAgent`: Main conversation orchestration
  - `ModerationAgent`: Content filtering and safety
  - `AnalyzerAgents`: Various analysis capabilities
  - `SummaryAgents`: Session and stage summaries

### 2. Factory Pattern
- `app_factory.py` creates application instances
- Centralized configuration and initialization
- Dependency injection support
- Environment-specific setup

### 3. Middleware Pipeline
- Security middleware for request validation
- Rate limiting for API protection
- Error handling and logging
- Cross-cutting concerns separation

### 4. State Machine Pattern
- FSM-based conversation flow
- Defined coaching stages and transitions
- State persistence across sessions
- Predictable conversation progression

### 5. Strategy Pattern (Analyzers)
- Base analyzer interface
- Pluggable analysis strategies:
  - Context analysis
  - Content analysis
  - Emotion detection
  - Stage transition logic
- Runtime strategy selection

## Data Patterns

### Database Architecture
- **Primary Store**: PostgreSQL with extensions
- **Vector Store**: pgvector for embeddings
- **Graph Store**: AGE extension for relationships
- **Memory System**: mem0ai integration
- **Search**: LightRAG for graph-based retrieval

### Data Access Patterns
- Repository pattern for data access
- Async/await for all I/O operations
- Connection pooling for performance
- Transaction management with proper rollback

## Integration Patterns

### External Service Integration
- Azure OpenAI for LLM capabilities
- Adapter pattern for service abstraction
- Circuit breaker for resilience
- Retry with exponential backoff

### API Design Patterns
- Resource-based routing
- Consistent error responses
- Pagination for large datasets
- Rate limiting per endpoint

## Security Patterns

### Authentication & Authorization
- Token-based authentication
- Role-based access control (planned)
- API key validation
- Request signature verification

### Data Protection
- Environment variables for secrets
- No hardcoded credentials
- Secure defaults
- Input validation at boundaries

## Error Handling Patterns

### Fail-Fast Principle
- Critical configuration validation on startup
- Early detection of missing dependencies
- Clear error messages for misconfiguration

### Graceful Degradation
- Fallback for optional services
- Default responses when services unavailable
- Feature flags for experimental features
- Logging without interrupting flow

## Async Patterns

### Concurrency Model
- AsyncIO for concurrent operations
- Task-based parallelism
- Proper context managers
- Resource cleanup guarantees

### Event-Driven Components
- Async event handlers
- Non-blocking I/O throughout
- Streaming responses where applicable
- WebSocket support (future)

## Testing Patterns

### Test Organization
- Unit tests for individual components
- Integration tests for workflows
- Fixture-based test data
- Async test support with pytest-asyncio

### Mock Strategies
- Dependency injection for testability
- Mock external services
- In-memory database for tests
- Deterministic test execution

## Deployment Patterns

### CI/CD Pipeline
- Trunk-based development
- Automated testing on commit
- Environment-specific configurations
- Blue-green deployments (production)

### Container Strategy
- Docker for consistency
- Multi-stage builds
- Minimal runtime images
- Health check endpoints

## Code Organization Patterns

### Module Structure
- Domain-driven design
- Clear separation of concerns
- Single responsibility principle
- Explicit dependencies

### Naming Conventions
- Descriptive function/class names
- Consistent suffix patterns (_agent, _service, _model)
- Clear intent communication
- Self-documenting code

## Performance Patterns

### Optimization Strategies
- Lazy loading where appropriate
- Caching for expensive operations
- Batch processing for bulk operations
- Efficient query patterns

### Scalability Considerations
- Stateless service design
- Horizontal scaling capability
- Database connection pooling
- Async processing for long tasks