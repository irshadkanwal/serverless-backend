---
created: 2025-09-22T18:29:15Z
last_updated: 2025-09-22T18:29:15Z
version: 1.0
author: Claude Code PM System
---

# Project Structure

## Root Directory Layout
```
serverless-backend/
├── app/                    # Main application code
├── ci-cd/                  # CI/CD configurations and scripts
├── tests/                  # Test suite
├── .claude/               # Claude Code context and configuration
│   ├── context/          # Project context documentation
│   └── scripts/          # Automation scripts
├── .github/               # GitHub Actions workflows
├── pyproject.toml         # Python project configuration
├── uv.lock               # Dependency lock file
├── README.md             # Project documentation
└── .venv/                # Virtual environment (local)
```

## Core Application Structure (`app/`)
```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── app_factory.py          # Application factory pattern
├── agents/                 # Agent implementations
│   ├── base_agent.py      # Base agent interface
│   ├── coaching_agent.py  # Main coaching logic
│   ├── moderation_agent.py # Content moderation
│   ├── analyzer/          # Analysis components
│   │   ├── base_analyzer.py
│   │   ├── context_analyzer.py
│   │   ├── content_analyzer.py
│   │   ├── emotion_analyzer.py
│   │   └── stage_transition_analyzer.py
│   └── summary/           # Summary generation
│       ├── session_summary_agent.py
│       └── stage_summary_agent.py
├── api/                    # API endpoints
│   └── routes/            # API route definitions
├── middleware/             # Middleware components
│   ├── __init__.py
│   ├── middleware.py      # General middleware
│   └── security.py        # Security middleware
├── models/                 # Data models
│   └── analyzer_model.py
├── prompts/               # Prompt templates (markdown-based)
├── services/              # Business logic services
├── storage/               # Data storage layers
├── util/                  # Utility modules
│   ├── config.py          # Configuration management
│   ├── constants.py       # Application constants
│   ├── errors.py          # Error handling
│   └── helpers.py         # Helper functions
└── state_machine/         # FSM implementation
```

## CI/CD Structure (`ci-cd/`)
```
ci-cd/
├── db/                    # Database setup
│   └── build-deploy.sh    # PostgreSQL container setup
├── docker-compose.yml     # Local development stack
└── Dockerfile            # Application container
```

## Test Structure (`tests/`)
```
tests/
├── __init__.py
├── unit/                  # Unit tests
├── integration/           # Integration tests
└── fixtures/             # Test fixtures and mocks
```

## Key File Patterns
- **Python modules**: `*.py` - Core application logic
- **Markdown prompts**: `app/prompts/*.md` - Coaching prompts
- **Configuration**: `pyproject.toml`, `.env` - Project settings
- **Lock files**: `uv.lock` - Pinned dependencies
- **Scripts**: `*.sh` - Automation and deployment

## Module Naming Conventions
- **Agents**: `*_agent.py` - Agent implementations
- **Analyzers**: `*_analyzer.py` - Analysis components
- **Models**: `*_model.py` - Data models
- **Services**: `*_service.py` - Business logic
- **Routes**: `*_routes.py` - API endpoints

## Import Organization
- Standard library imports first
- Third-party imports second
- Local application imports last
- Absolute imports preferred over relative

## File Organization Principles
1. **Separation of Concerns**: Clear boundaries between layers
2. **Domain-Driven Structure**: Organized by business functionality
3. **Agent-Based Architecture**: Specialized agents for different tasks
4. **Middleware Pattern**: Cross-cutting concerns in middleware
5. **Factory Pattern**: Application initialization via factory