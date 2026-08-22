"""Brasaland FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.incidents import router as incidents_router
from database import count_suppliers
from routes.suppliers import router as suppliers_router
from seed import run_seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Tech lead: DB must never be empty during a demo.
    if count_suppliers() == 0:
        inserted = run_seed()
        print(f"Startup seed: inserted {inserted} suppliers into TinyDB.")
    yield


app = FastAPI(
    title="Brasaland API",
    description="Internal Brasaland APIs: incidents analysis and supplier directory.",
    version="0.2.0",
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

app.include_router(incidents_router)
app.include_router(suppliers_router)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}
