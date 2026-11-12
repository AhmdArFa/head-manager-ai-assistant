from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.db import configured_database_path, initialize_database
from app.orchestrator import ChiefOrchestrator
from app.schemas import AskRequest, AskResponse, HealthResponse


def create_app(database_path: str | Path | None = None) -> FastAPI:
    db_path = Path(database_path) if database_path is not None else configured_database_path()
    initialize_database(db_path)
    orchestrator = ChiefOrchestrator(str(db_path))

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    application = FastAPI(
        title="Head Manager AI Assistant",
        description="Step 1: grounded company Q&A from a local read-only data source.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="head-manager-ai-assistant")

    @application.post("/api/v1/ask", response_model=AskResponse, tags=["assistant"])
    def ask(request: AskRequest) -> AskResponse:
        return orchestrator.run(request.question.strip())

    return application


app = create_app()
