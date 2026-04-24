from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial
import logging
import logging.config

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_CONTENT,
)

from src.agents.model_factory import build_openrouter_http_client, build_openrouter_model
from src.agents.sample.agent import build_sample_agent
from src.api_server.helpers.utils import build_validation_error_detail
from src.api_server.responses import response_400, response_401, response_403, response_500
from src.api_server.routers import agent, user
from src.config.config import config
from src.config.logging_config import get_logging_config
from src.constants import VERSION_PREFIX
from src.models.problem_details import ProblemDetails

logging.config.dictConfig(get_logging_config(config.LOG_FILE_PATH, config.LOG_LEVEL))
logger = logging.getLogger(__name__)
domain_pattern = r"http:\/\/localhost:3000"  # TODO: update with real domains


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    http_client = build_openrouter_http_client()
    model = build_openrouter_model(http_client=http_client)
    app.state.default_agent = build_sample_agent(model=model)
    app.state.openrouter_http_client = http_client
    try:
        yield
    finally:
        await app.state.openrouter_http_client.aclose()


def build_app() -> FastAPI:
    _app = FastAPI(
        title="boilerplate-api",
        description="Boilerplate API",
        version="0.0.1",  # TODO: add support for automatic versioning
        openapi_url=f"/{VERSION_PREFIX}/swagger.json",
        docs_url="/",
        debug=not config.IS_PROD,
        responses=response_400 | response_401 | response_403 | response_500,
        lifespan=app_lifespan,
    )

    # Add routers
    _app.include_router(user.router, tags=["users"], prefix=f"/{VERSION_PREFIX}")
    _app.include_router(agent.router, tags=["agents"], prefix=f"/{VERSION_PREFIX}")

    _app.add_middleware(
        CORSMiddleware,  # ty: ignore[invalid-argument-type]
        allow_origin_regex=domain_pattern,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _app.add_middleware(CorrelationIdMiddleware)  # outermost — assigns trace ID before all other processing

    _app.openapi()

    return _app


app = build_app()


STATUSES = [
    (HTTP_400_BAD_REQUEST, "Bad Request"),
    (HTTP_401_UNAUTHORIZED, "Unauthorized"),
    (HTTP_403_FORBIDDEN, "Unauthorized"),
    (HTTP_404_NOT_FOUND, "Not Found"),
    (HTTP_405_METHOD_NOT_ALLOWED, "Method Not Allowed"),
    (HTTP_409_CONFLICT, "Conflict"),
    (HTTP_422_UNPROCESSABLE_CONTENT, "Unprocessable Content"),
]


async def generic_error_handler(request: Request, exc: HTTPException, status_code: int, title: str) -> JSONResponse:
    problem_details = ProblemDetails(detail=exc.detail, status=status_code, title=title)
    return JSONResponse(jsonable_encoder(problem_details), status_code=status_code)


for status, msg in STATUSES:
    app.add_exception_handler(status, partial(generic_error_handler, status_code=status, title=msg))


@app.exception_handler(StarletteHTTPException)
async def other_errors_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle all other HTTP errors"""
    if exc.status_code >= 500:
        logger.error(jsonable_encoder(exc))
        problem_details = ProblemDetails(
            detail="Internal Server Error", status=exc.status_code, title="Internal Server Error"
        )
    else:
        problem_details = ProblemDetails(detail=exc.detail, status=exc.status_code, title="Error")
    return JSONResponse(jsonable_encoder(problem_details), status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    problem_details = ProblemDetails(
        detail=str(build_validation_error_detail(exc.errors())), status=HTTP_400_BAD_REQUEST, title="Validation Error"
    )
    return JSONResponse(jsonable_encoder(problem_details), status_code=HTTP_400_BAD_REQUEST)
