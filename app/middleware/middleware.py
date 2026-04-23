from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.dependencies import get_limiter
from app.middleware.security import add_security_headers
from app.util.constants import ALLOWED_HEADERS, ALLOWED_METHODS, ALLOWED_ORIGINS


def setup_rate_limiting(app: FastAPI):
    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def setup_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
    )


def setup_security_middleware(app: FastAPI):
    app.middleware("http")(add_security_headers)


def setup_all_middleware(app: FastAPI):
    setup_rate_limiting(app)
    setup_cors(app)
    setup_security_middleware(app)
