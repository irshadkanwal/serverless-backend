import secrets

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from app.util.constants import API_KEY, API_KEY_NAME

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
):
    if api_key_query and secrets.compare_digest(api_key_query, API_KEY):
        return api_key_query
    if api_key_header and secrets.compare_digest(api_key_header, API_KEY):
        return api_key_header

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Check if this is a docs route
    is_docs_route = request.url.path in ["/docs", "/redoc", "/openapi.json"]

    # Base security headers
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    # Apply relaxed CSP for docs routes, strict CSP for everything else
    if is_docs_route:
        security_headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "object-src 'none'; frame-ancestors 'none';"
        )
    else:
        security_headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "font-src 'self'; object-src 'none'; frame-ancestors 'none';"
        )

    response.headers.update(security_headers)
    return response
