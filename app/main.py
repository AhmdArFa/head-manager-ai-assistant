from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.db import configured_database_path, initialize_database, is_mssql_configured
from app.orchestrator import ChiefOrchestrator
from app.schemas import AskRequest, AskResponse, HealthResponse


def create_app(database_path: str | Path | None = None) -> FastAPI:
    if database_path is not None:
        db_path = Path(database_path)
        initialize_database(db_path)
        orchestrator = ChiefOrchestrator(database_target=str(db_path), backend_type="sqlite")
    elif is_mssql_configured():
        orchestrator = ChiefOrchestrator(database_target=None, backend_type="mssql")
    else:
        db_path = configured_database_path()
        initialize_database(db_path)
        orchestrator = ChiefOrchestrator(database_target=str(db_path), backend_type="sqlite")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    application = FastAPI(
        title="Head Manager AI Assistant",
        description="Grounded company Q&A from 4S SQL Server or local data source.",
        version="0.2.0",
        lifespan=lifespan,
    )
    demo_dir = Path(__file__).resolve().parent.parent / "demo"
    application.mount("/demo", StaticFiles(directory=demo_dir, html=True), name="demo")

    @application.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/demo/")

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="head-manager-ai-assistant")

    @application.post("/api/v1/ask", response_model=AskResponse, tags=["assistant"])
    def ask(request: AskRequest) -> AskResponse:
        return orchestrator.run(request.question.strip())

    return application


app = create_app()
