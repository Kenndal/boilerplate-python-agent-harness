---
name: pydantic-ai alignment review
overview: Review current pydantic-ai integration and align the project with the latest pydantic-ai patterns while preserving existing FastAPI/service-layer architecture.
todos:
  - id: audit-versioning
    content: Set bounded pydantic-ai dependency policy and document upgrade cadence
    status: completed
  - id: lifecycle-refactor
    content: Introduce managed model/provider/http client lifecycle tied to app startup/shutdown
    status: completed
  - id: agent-di-refactor
    content: Refactor global sample agent into DI-driven factory and registry integration
    status: pending
  - id: history-token-budget
    content: Add token-aware history clipping configuration and implementation
    status: pending
  - id: tool-error-semantics
    content: Improve tool error structure and runner mapping/logging consistency
    status: completed
  - id: pydantic-ai-tests
    content: Add runner mapping tests and pydantic-ai-native model/tool behavior tests
    status: pending
isProject: false
---

# Pydantic-AI Alignment Plan

## Current State Snapshot
- The project already uses modern pydantic-ai primitives (`Agent`, `RunContext`, `OpenAIChatModel`, `ModelMessage`) in:
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/sample/agent.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/sample/agent.py)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/model_factory.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/model_factory.py)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/runner.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/runner.py)
- Dependency constraint is open-ended (`pydantic-ai-slim[openai]>=1.85.0`) in [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/pyproject.toml`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/pyproject.toml), with lock currently at `1.85.0`.

## Recommended Changes (Priority Order)

### 1) Manage model/provider lifecycle explicitly (High)
- **Why:** `httpx.AsyncClient` is created in `build_openrouter_model()` and not explicitly closed, which risks leaked connections in long-lived processes/tests.
- **Change:** Introduce app-managed lifecycle for model/provider client creation and shutdown via FastAPI lifespan/dependency container.
- **Files to update:**
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/model_factory.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/model_factory.py)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/api_server/deps.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/api_server/deps.py)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/api_server/main.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/api_server/main.py)

### 2) Replace import-time singleton agent with factory/DI (High)
- **Why:** Global `sample_agent` instantiation makes runtime config and test isolation harder; latest patterns favor constructing agents via DI/factory.
- **Change:** Refactor `sample_agent` to `build_sample_agent(model=...)` and resolve an agent instance through DI (`get_default_agent` becomes provider-backed).
- **Files to update:**
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/sample/agent.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/sample/agent.py)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/registry.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/registry.py)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/api_server/deps.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/api_server/deps.py)

### 3) Make history clipping token-aware (Medium)
- **Why:** Count-based clipping (`AGENT_MAX_HISTORY_MESSAGES`) can still overflow context windows with long messages/tool payloads.
- **Change:** Add token-budget-based clipping strategy with config fallback to message-count clipping.
- **Files to update:**
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/services/agent_conversation_service.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/services/agent_conversation_service.py)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/config/config.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/config/config.py)

### 4) Improve tool failure semantics (Medium)
- **Why:** `RuntimeError` from tools loses structured signal; better semantics improve recoverability and troubleshooting.
- **Change:** Introduce a small typed tool error path (or domain exception mapping) and preserve structured details in runner logs/error mapping.
- **Files to update:**
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/tools/user_tools.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/tools/user_tools.py)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/runner.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/agents/runner.py)

### 5) Expand pydantic-ai-native tests (Medium)
- **Why:** Current tests are strong around history conversion/persistence, but there are no dedicated tests for runner exception mapping and model/tool behavior via pydantic-ai test primitives.
- **Change:** Add unit tests for `AgentRunner` mapping and at least one agent/tool behavior test using pydantic-ai testing patterns (`TestModel` or function-model equivalent).
- **Files to add/update:**
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/tests/unit/agents/test_runner.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/tests/unit/agents/test_runner.py)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/tests/unit/agents/test_sample_agent.py`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/src/tests/unit/agents/test_sample_agent.py)

### 6) Tighten dependency/version strategy for safe upgrades (Low)
- **Why:** `>=` on pydantic-ai without upper bound can unexpectedly pull breaking changes when lock is refreshed.
- **Change:** Use bounded ranges (e.g., `>=1.85,<2`) and document upgrade cadence.
- **Files to update:**
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/pyproject.toml`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/pyproject.toml)
  - [`/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/README.md`](/Users/jakubprzybylo/projects/boilerplate-python-agent-harness/README.md)

## What Should Stay As-Is
- Custom history persistence bridge is reasonable and aligns with your database-first architecture; keep it, but add guardrail tests for future pydantic-ai message-shape evolution.
- Existing service-layer orchestration and Result-pattern boundaries are solid and should remain unchanged.

## Suggested Execution Phases
- **Phase A (stability):** lifecycle + DI refactor (items 1-2)
- **Phase B (resilience):** token-aware history + tool error semantics (items 3-4)
- **Phase C (maintainability):** tests + dependency policy (items 5-6)