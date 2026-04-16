from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, ClassVar
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama

from mitonexus.agents.state import MitoNexusState
from mitonexus.config import get_settings
from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import AgentRun
from mitonexus.observability.langfuse_setup import get_langfuse_callback


@dataclass
class AgentExecutionContext:
    """Per-invocation execution context."""

    tool_calls: list[dict[str, object]] = field(default_factory=list)
    callback: Any | None = None
    langfuse_trace_id: str | None = None


def _serialize_messages(messages: list[BaseMessage]) -> list[dict[str, object]]:
    """Convert LangChain messages to JSON-compatible dicts."""
    encoded = jsonable_encoder(messages)
    return encoded if isinstance(encoded, list) else []


class BaseAgent(ABC):
    """Base class for MitoNexus workflow agents."""

    name: str
    model_name: str | None = None
    temperature: float = 0.1
    tools: ClassVar[list[BaseTool]] = []

    def __init__(self, llm: Any | None = None) -> None:
        self._llm = llm

    async def __call__(self, state: MitoNexusState) -> dict[str, object]:
        started = perf_counter()
        context = AgentExecutionContext(
            callback=get_langfuse_callback(
                user_id=state["patient_id"],
                session_id=state["report_id"],
            )
        )

        output: dict[str, object] | None = None
        try:
            output = await self._execute(state, context)
            context.langfuse_trace_id = self._extract_trace_id(context)
            return output
        finally:
            duration_ms = int((perf_counter() - started) * 1000)
            await self._persist_run(
                report_id=state.get("report_id"),
                state=state,
                output=output,
                context=context,
                duration_ms=duration_ms,
            )

    @abstractmethod
    async def _execute(
        self,
        state: MitoNexusState,
        context: AgentExecutionContext,
    ) -> dict[str, object]:
        """Run the agent against the current workflow state."""

    def get_llm(self) -> Any | None:
        """Return the configured LLM, creating it lazily when needed."""
        if self.model_name is None:
            return None
        if self._llm is None:
            settings = get_settings()
            llm: Any = ChatOllama(
                model=self.model_name,
                base_url=settings.ollama_host,
                temperature=self.temperature,
            )
            if self.tools and hasattr(llm, "bind_tools"):
                llm = llm.bind_tools(self.tools)
            self._llm = llm
        return self._llm

    async def invoke_summary_llm(
        self,
        prompt: str,
        context: AgentExecutionContext,
    ) -> str | None:
        """Generate a short summary with the configured LLM when available."""
        llm = self.get_llm()
        if llm is None:
            return None

        config: dict[str, object] | None = None
        if context.callback is not None:
            config = {"callbacks": [context.callback]}

        try:
            response = await llm.ainvoke(prompt, config=config)
        except Exception:
            return None

        context.langfuse_trace_id = self._extract_trace_id(context)
        content = getattr(response, "content", response)
        if isinstance(content, str):
            return content.strip() or None
        if isinstance(content, list):
            text_parts = [part for part in content if isinstance(part, str)]
            return "\n".join(text_parts).strip() or None
        return str(content).strip() or None

    async def call_tool(
        self,
        tool: BaseTool,
        args: dict[str, object],
        context: AgentExecutionContext,
    ) -> Any:
        """Invoke a LangChain tool and record the call."""
        result = await tool.ainvoke(args)
        context.tool_calls.append(
            {
                "tool_name": tool.name,
                "args": args,
                "result": jsonable_encoder(result),
            }
        )
        return result

    def build_message(self, content: str) -> list[AIMessage]:
        """Build a single AI message payload for state updates."""
        return [AIMessage(content=content)]

    def _extract_trace_id(self, context: AgentExecutionContext) -> str | None:
        callback = context.callback
        trace_id = getattr(callback, "last_trace_id", None)
        return trace_id if isinstance(trace_id, str) and trace_id else None

    async def _persist_run(
        self,
        *,
        report_id: str | None,
        state: MitoNexusState,
        output: dict[str, object] | None,
        context: AgentExecutionContext,
        duration_ms: int,
    ) -> None:
        if not report_id:
            return

        serialized_state = jsonable_encoder(
            {
                **state,
                "messages": _serialize_messages(state.get("messages", [])),
            }
        )
        serialized_output = jsonable_encoder(output) if output is not None else None

        async with AsyncSessionLocal() as session:
            session.add(
                AgentRun(
                    report_id=UUID(report_id),
                    agent_name=self.name,
                    state=serialized_state,
                    tool_calls=context.tool_calls,
                    output=serialized_output,
                    duration_ms=duration_ms,
                    langfuse_trace_id=context.langfuse_trace_id,
                )
            )
            await session.commit()
