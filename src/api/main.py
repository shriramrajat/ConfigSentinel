"""
api.main
~~~~~~~~

FastAPI application factory for ConfigSentinel.

Usage
-----
Run the development server from the repository root:

    uvicorn src.api.main:app --reload

The OpenAPI schema is available at:

    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
    http://localhost:8000/openapi.json

Production deployment
---------------------
Replace the uvicorn invocation with an appropriate ASGI server configuration.
Set the ``CONFIGSENTINEL_ALLOW_ORIGINS`` environment variable to restrict CORS.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import ALLOW_ORIGINS, API_VERSION, PRODUCT_DESCRIPTION, PRODUCT_NAME
from src.api.errors import (
    InvalidInputError,
    handle_invalid_input,
    handle_unexpected_error,
    handle_validation_error,
)
from src.api.routes import router


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns a fully wired application instance.
    Using a factory function makes the app testable without import side-effects.
    """
    app = FastAPI(
        title=PRODUCT_NAME,
        version=API_VERSION,
        description=PRODUCT_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ---- CORS ---------------------------------------------------------------
    # Default: allow all origins (suitable for development / internal tools).
    # Set CONFIGSENTINEL_ALLOW_ORIGINS in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOW_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Accept"],
    )

    # ---- Exception handlers -------------------------------------------------
    # Ordered from most specific to least specific.
    app.add_exception_handler(InvalidInputError, handle_invalid_input)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, handle_unexpected_error)  # type: ignore[arg-type]

    # ---- Routes -------------------------------------------------------------
    app.include_router(router)

    from src.api.mapping_routes import router as mapping_router
    app.include_router(mapping_router)

    from src.api.intelligence_routes import router as intelligence_router
    app.include_router(intelligence_router)

    from src.api.phase3_routes import router as phase3_router
    app.include_router(phase3_router)

    return app


#: Module-level app instance — used by uvicorn and the test client.
app = create_app()
