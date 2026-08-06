from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.incidents import router as incidents_router

app = FastAPI(
    title="Brasaland Incident API",
    description="Internal API for after-sales / operations incident CSV analysis.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3102",
        "http://127.0.0.1:3102",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
