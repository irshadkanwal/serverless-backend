class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(AppError):
    """Database-related errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class Auth0Error(AppError):
    """Auth0-related errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class ValidationError(AppError):
    """Data validation errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class KnowledgeGraphError(AppError):
    """Error related to knowledge graph operations."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)


class LLMError(AppError):
    """LLM-related errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)
