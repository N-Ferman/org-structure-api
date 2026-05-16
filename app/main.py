import logging

from fastapi import FastAPI

from app.api.departments import router as departments_router


logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Organization Structure API",
    version="1.0.0",
    description="API for departments, employees and organization tree management.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(departments_router)