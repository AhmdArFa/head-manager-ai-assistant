from uuid import uuid4

from app.agents.data_agent import DataAgent
from app.schemas import AskResponse, TraceStep


class ChiefOrchestrator:
    """Minimal deterministic supervisor; new specialist agents can be added behind this boundary."""

    def __init__(self, database_path: str):
        self.data_agent = DataAgent(database_path)

    def run(self, question: str) -> AskResponse:
        result = self.data_agent.answer_question(question)
        trace = [
            TraceStep(
                step="route_question",
                component="chief_orchestrator",
                status="completed",
                detail=f"Routed to data_agent with intent '{result.intent}'.",
            )
        ]
        if result.source:
            trace.append(
                TraceStep(
                    step="query_data",
                    component="data_agent",
                    status="completed",
                    detail=f"Executed reviewed query '{result.source['query_id']}' read-only.",
                )
            )
        else:
            trace.append(
                TraceStep(
                    step="query_data",
                    component="data_agent",
                    status="skipped",
                    detail="No reviewed query matches this question; no database query was run.",
                )
            )
        trace.append(
            TraceStep(
                step="compose_answer",
                component="response_composer",
                status="completed",
                detail="Answer composed from returned database rows; no model-generated facts.",
            )
        )
        return AskResponse(
            request_id=str(uuid4()),
            question=question,
            intent=result.intent,
            answer=result.answer,
            data=result.data,
            sources=[result.source] if result.source else [],
            trace=trace,
        )
