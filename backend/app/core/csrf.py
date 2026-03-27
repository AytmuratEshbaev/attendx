"""CSRF protection middleware.

For this API (JWT/API-Key auth), CSRF is not required for /api/ routes.
The middleware is included for completeness in case cookie-based sessions
are added in the future.
"""

import secrets

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection for state-changing requests.

    API endpoints using Bearer token / API Key auth are exempt — token-based
    auth is inherently CSRF-safe.  Only non-/api/ routes with cookies are
    checked.
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip CSRF check for all /api/ routes (token-based auth)
        if request.url.path.startswith("/api/"):
            return await call_next(request)

        # For non-API unsafe methods, verify CSRF token
        if request.method not in self.SAFE_METHODS:
            csrf_token = request.headers.get("X-CSRF-Token")
            session_token = request.cookies.get("csrf_token")

            if (
                not csrf_token
                or not session_token
                or not secrets.compare_digest(csrf_token, session_token)
            ):
                return JSONResponse(
                    status_code=403,
                    content={
                        "success": False,
                        "error": {
                            "code": "CSRF_FAILED",
                            "message": "CSRF token mismatch",
                        },
                    },
                )

        response = await call_next(request)

        # Issue a CSRF cookie if the client doesn't have one yet
        if "csrf_token" not in request.cookies:
            token = secrets.token_urlsafe(32)
            response.set_cookie(
                "csrf_token",
                token,
                httponly=False,  # JavaScript must be able to read it
                samesite="strict",
                secure=True,
                max_age=3600,
            )

        return response
