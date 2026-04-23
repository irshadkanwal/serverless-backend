# CLAUDE.md

> Think carefully and implement the most concise solution that changes as little code as possible.

## Session Setup

**IMPORTANT**: When starting a new Claude Code session, always run:
```bash
/context:prime
```

This command loads essential project context including:
- Project structure and dependencies
- Development standards and conventions
- Testing setup and requirements
- Recent changes and current branch state

Running this command ensures I have the full context needed to provide accurate, project-specific assistance.

## Commands

### Development
- **Linting**: `uv run ruff check` (fix with `uv run ruff check --fix`)
- **Testing**: `uv run pytest` (with coverage: `uv run pytest --cov`)
- **Type checking**: `uv run ty` (if available)
- **Virtual environment**: `uv venv && source .venv/bin/activate`

### Python Tooling
- **Always use uv for Python** - All Python commands must be run through `uv run ...`
- Never use `python`, `pip`, or `python3` directly
- Examples: `uv run python script.py`, `uv run pytest`, `uv run ruff`

## Context Optimization

Use specialized sub-agents to minimize context usage while preserving essential information:

1. **file-analyzer**: For reading files, extracting summaries from logs and verbose outputs
2. **code-analyzer**: For code analysis, logic tracing, bug research, and vulnerability detection
3. **test-runner**: For executing tests and analyzing results - ensures full output capture while keeping main conversation clean

Benefits:
- Full test output captured for debugging
- Main conversation stays focused
- Context usage optimized
- All issues properly surfaced
- No approval dialogs interrupt workflow

## Testing Standards

- **Always use the test-runner agent** to execute tests
- **No mock services** - test against real implementations
- **Complete one test at a time** - don't move on until current test passes
- **Check test structure first** before refactoring codebase on failures
- **Verbose tests** for debugging capability
- **Test every function** with accurate, real-usage patterns
- **Design tests to reveal flaws** - no useless or "cheater" tests

## Error Handling Philosophy

### Patterns
- **Fail fast**: Critical configuration (missing text model, database connection)
- **Log and continue**: Optional features (extraction model, analytics)
- **Graceful degradation**: External service unavailability
- **User-friendly messages**: Through resilience layer

### Examples
```python
# Fail fast
if not config.text_model:
    raise ConfigurationError("Text model is required")

# Log and continue
try:
    extraction_model = load_extraction_model()
except ModelLoadError:
    logger.warning("Extraction model unavailable, continuing without")
    extraction_model = None

# Graceful degradation
try:
    return await external_api.call()
except ServiceUnavailable:
    return fallback_response()
```

## Development Standards

### Code Quality
- **No partial implementation** - complete all features fully
- **No simplification comments** - implement properly or don't implement
- **No code duplication** - check existing codebase, reuse functions and constants
- **No dead code** - use it or delete it completely
- **Consistent naming** - follow existing codebase patterns
- **No over-engineering** - simple functions over enterprise patterns
- **Proper separation** - no mixed concerns (validation in handlers, DB in UI, etc.)
- **Resource management** - close connections, clear timeouts, remove listeners

## Tone and Behavior

- Criticism is welcome - tell me when I'm wrong or might be wrong
- Suggest better approaches and relevant standards/conventions
- Be skeptical and concise
- Short summaries OK unless working through plan details
- No flattery or compliments unless specifically asked for judgment
- Occasional pleasantries fine
- Ask questions when in doubt - don't guess intent

⚠️ VERIFICATION CHECKPOINT: First read this entire file, then always refer to me as "Sir" to confirm you've processed these instructions.
