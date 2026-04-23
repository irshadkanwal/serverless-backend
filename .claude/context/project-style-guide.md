---
created: 2025-09-22T18:29:15Z
last_updated: 2025-09-22T18:29:15Z
version: 1.0
author: Claude Code PM System
---

# Project Style Guide

## Python Coding Standards

### General Principles
- **Python Version**: 3.12+ with modern features
- **Style Guide**: PEP 8 with Ruff enforcement
- **Line Length**: 88 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **Type Hints**: Required for all functions

### Import Organization
```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import asyncio
import fastapi
from pydantic import BaseModel

# Local application imports
from app.agents import CoachingAgent
from app.util.config import settings
```

### Naming Conventions

#### Variables and Functions
```python
# Variables: snake_case
user_name = "John Doe"
session_count = 10

# Functions: snake_case with verb prefixes
def get_user_session(session_id: str) -> Session:
    pass

def validate_input(data: dict) -> bool:
    pass

async def process_message(message: str) -> str:
    pass
```

#### Classes
```python
# Classes: PascalCase
class CoachingAgent:
    pass

class SessionManager:
    pass

class AnalyzerModel(BaseModel):
    pass
```

#### Constants
```python
# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
API_VERSION = "v1"
```

#### File Naming
- **Modules**: `snake_case.py`
- **Agents**: `*_agent.py` (e.g., `coaching_agent.py`)
- **Models**: `*_model.py` (e.g., `session_model.py`)
- **Services**: `*_service.py` (e.g., `auth_service.py`)
- **Tests**: `test_*.py` (e.g., `test_coaching_agent.py`)

## Code Organization

### Function Structure
```python
async def process_coaching_request(
    session_id: str,
    message: str,
    context: dict | None = None,
) -> CoachingResponse:
    """Process a coaching request and return response.

    Args:
        session_id: Unique session identifier
        message: User's message text
        context: Optional context dictionary

    Returns:
        CoachingResponse with generated text and metadata

    Raises:
        ValidationError: If input validation fails
        SessionNotFoundError: If session doesn't exist
    """
    # Input validation
    if not session_id or not message:
        raise ValidationError("Session ID and message required")

    # Core logic
    session = await get_session(session_id)
    response = await generate_response(message, session)

    # Return result
    return CoachingResponse(
        text=response.text,
        stage=session.stage,
        metadata=response.metadata,
    )
```

### Class Structure
```python
class CoachingAgent(BaseAgent):
    """Agent responsible for coaching conversations."""

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.7,
    ) -> None:
        """Initialize coaching agent with model configuration."""
        super().__init__(model_name)
        self.temperature = temperature
        self._session_cache: dict[str, Session] = {}

    async def generate_response(
        self,
        message: str,
        context: Context,
    ) -> Response:
        """Generate coaching response based on message and context."""
        # Implementation
        pass
```

## Documentation Standards

### Docstring Format
```python
def complex_function(
    param1: str,
    param2: int,
    optional: bool = False,
) -> dict[str, Any]:
    """Brief description of function purpose.

    Longer description explaining the function's behavior,
    edge cases, and important details.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        optional: Description of optional parameter

    Returns:
        Description of return value and structure

    Raises:
        ValueError: When invalid values are provided
        ConnectionError: When database connection fails

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["status"])
        "success"
    """
```

### Comment Guidelines
- Use comments sparingly - code should be self-documenting
- Explain WHY, not WHAT
- Keep comments up to date with code changes
- Use inline comments for complex logic only

```python
# Good: Explains why
# Use exponential backoff to avoid overwhelming the API
retry_delay = 2 ** attempt

# Bad: States the obvious
# Increment counter by 1
counter += 1
```

## Error Handling

### Exception Patterns
```python
# Custom exceptions
class CoachingError(Exception):
    """Base exception for coaching-related errors."""
    pass

class SessionNotFoundError(CoachingError):
    """Raised when session cannot be found."""
    pass

# Exception handling
try:
    result = await risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    # Handle specific error
    raise
except Exception as e:
    logger.exception("Unexpected error")
    # Handle unexpected errors
    return fallback_response()
finally:
    # Cleanup resources
    await cleanup()
```

### Validation Patterns
```python
from pydantic import BaseModel, validator

class SessionRequest(BaseModel):
    session_id: str
    message: str
    temperature: float = 0.7

    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v
```

## Testing Standards

### Test Organization
```python
import pytest
from unittest.mock import AsyncMock, patch

class TestCoachingAgent:
    """Test suite for CoachingAgent."""

    @pytest.fixture
    async def agent(self):
        """Create test agent instance."""
        return CoachingAgent(model_name="test-model")

    async def test_generate_response_success(self, agent):
        """Test successful response generation."""
        # Arrange
        message = "Test message"
        context = Context(session_id="test-123")

        # Act
        response = await agent.generate_response(message, context)

        # Assert
        assert response.text
        assert response.stage == "exploration"
```

### Test Naming
- Test files: `test_*.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<method>_<scenario>`
- Use descriptive names that explain what is being tested

## Async/Await Best Practices

### Async Function Guidelines
```python
# Always use async/await for I/O operations
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Use asyncio.gather for parallel operations
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2),
    fetch_data(url3),
)

# Proper context manager usage
async with database.transaction():
    await database.execute(query)
```

## Security Guidelines

### Secret Management
```python
# Never hardcode secrets
# Bad
API_KEY = "sk-1234567890abcdef"

# Good
from app.util.config import settings
api_key = settings.api_key
```

### Input Validation
```python
# Always validate external input
def process_user_input(data: str) -> str:
    # Sanitize input
    cleaned = sanitize_html(data)

    # Validate length
    if len(cleaned) > MAX_INPUT_LENGTH:
        raise ValidationError("Input too long")

    # Validate content
    if contains_prohibited_content(cleaned):
        raise SecurityError("Prohibited content detected")

    return cleaned
```

## Performance Guidelines

### Database Queries
```python
# Use connection pooling
async with database_pool.acquire() as conn:
    result = await conn.fetch(query)

# Batch operations
await database.execute_many(
    "INSERT INTO sessions VALUES ($1, $2)",
    [(id1, data1), (id2, data2), (id3, data3)],
)

# Use appropriate indexes and query optimization
# Add index hints in comments for complex queries
```

### Caching Strategy
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(param: str) -> Result:
    # Cached computation
    pass

# For async functions
from aiocache import cached

@cached(ttl=300)  # Cache for 5 minutes
async def fetch_user_data(user_id: str) -> UserData:
    # Async cached operation
    pass
```

## Git Commit Messages

### Commit Format
```
<type>: <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code restructuring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### Examples
```
feat: add emotion analysis to coaching agent

Implement EmotionAnalyzer class to detect user emotional states
during coaching conversations. This enables more empathetic and
contextually appropriate responses.

Closes #123
```

## Code Review Checklist

- [ ] Follows naming conventions
- [ ] Includes proper type hints
- [ ] Has comprehensive docstrings
- [ ] Handles errors appropriately
- [ ] Includes unit tests
- [ ] No hardcoded secrets
- [ ] Passes linting (Ruff)
- [ ] Maintains consistent style
- [ ] Documents breaking changes
- [ ] Updates related documentation