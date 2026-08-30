"""Brasaland FastAPI application entrypoint."""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from json import JSONDecodeError
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth.router import router as auth_router
from app.auth.seed import seed_auth_if_empty
from app.errors import PersistenceError
from app.profiles.router import router as profiles_router
from app.routers.incidents import router as incidents_router
from app.users.router import router as users_router
from database import count_suppliers
from routes.suppliers import router as suppliers_router
from seed import run_seed

logger = logging.getLogger("brasaland")

GENERIC_500 = (
    "Something went wrong. Try again or contact hello@brasaland.com."
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Tech lead: DB must never be empty during a demo.
    try:
        if count_suppliers() == 0:
            inserted = run_seed()
            print(f"Startup seed: inserted {inserted} suppliers.")
        auth_status = seed_auth_if_empty()
        print(f"Startup auth seed: {auth_status}.")
    except PersistenceError:
        logger.exception("Startup seed failed")
        print(
            "Startup seed failed. Check disk access and try again.",
            file=sys.stderr,
        )
    yield


app = FastAPI(
    title="Brasaland API",
    description=(
        "Internal Brasaland APIs: authentication, incidents analysis, "
        "and supplier directory."
    ),
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3101",
        "http://127.0.0.1:3101",
        "http://localhost:3102",
        "http://127.0.0.1:3102",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profiles_router)
app.include_router(incidents_router)
app.include_router(suppliers_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    detail = exc.detail
    if not isinstance(detail, str):
        detail = "Request could not be completed."
    headers = getattr(exc, "headers", None)
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
    )
    if headers:
        response.headers.update(headers)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    safe = []
    for err in exc.errors():
        safe.append(
            {
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
        )
    return JSONResponse(status_code=422, content={"detail": safe})


@app.exception_handler(JSONDecodeError)
async def json_decode_handler(
    _request: Request, _exc: JSONDecodeError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": "Request body must be valid JSON."},
    )


@app.exception_handler(PersistenceError)
async def persistence_exception_handler(
    _request: Request, exc: PersistenceError
) -> JSONResponse:
    logger.exception("Persistence error")
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    if isinstance(exc, StarletteHTTPException):
        return await http_exception_handler(request, exc)
    logger.exception("Unhandled server error")
    return JSONResponse(status_code=500, content={"detail": GENERIC_500})


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}
