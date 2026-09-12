# Lexi Agent (LExI)

Local EXecutive Intelligence (LExI) is an autonomous, self-improving agent runtime featuring persistent memory, procedural skill learning, tool execution, and scheduled automations. It is designed to operate locally and pairs exclusively with [`lexi-webui`](https://github.com/rkpjrpete/lexi-webui) as part of the [`lexi-core`](https://github.com/rkpjrpete/local-executive-intelligence) stack.

---

## 📦 Upstream Fork & Provenance

- **Upstream Repository**: [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent)
- **Forked Version**: **`v0.21.1`**
- **Base Commit**: `6e2b8e070d` (Released September 7, 2026)
- **Upstream License**: MIT

### Architecture & Responsibility Boundary
`lexi-agent` serves as the execution brain and intelligence core:
- **Owns Persona & Prompts**: Contains root identity (`SOUL.md`), context files, and system prompt assembly.
- **Owns Memory & Skills**: Manages long-term state (`MEMORY.md`, `USER.md`), FTS5 conversation recall, and procedural skills (`skills/`).
- **Owns Tool Execution**: Executes terminal commands, file I/O, web browsing, cron tasks, and subagent delegation.
- **Exposes Gateway API**: Provides an OpenAI-compatible chat completions and Gateway Runs API on port `8642`, serving both external API clients and `lexi-webui`.

---

## 🏛 Architecture

```text
[ lexi-webui (:8787) ] ───(Gateway Runs API / HTTP)───┐
                                                       ▼
[ CLI / TUI (lexi) ]   ───(In-Process Execution)────> [ Lexi Agent Engine (:8642) ]
                                                       │  • SOUL.md / System Persona
[ Host / Remote API ]  ───(OpenAPI :8642/v1)──────────┘  • Memory & Skills
                                                       │  • Autonomous Tool Loop
                                                       ▼
                                            [ vLLM Engine (:8000) ]
                                              (Gemma 4 12B AWQ)
```

---

## 🚀 Quick Start

### 1. Docker (Recommended via lexi-core)
`lexi-agent` runs as a core service in `lexi-core`:
```bash
cd /home/lexiroot/lexi-core
docker compose up -d
```

### 2. Interactive Terminal UI (TUI)
Interact with the agent directly inside the running container:
```bash
# Full interactive TUI
docker exec -it lexi-agent lexi

# Quick terminal chat
docker exec -it lexi-agent lexi chat

# Manage procedural skills
docker exec -it lexi-agent lexi skills
```

### 3. Gateway / OpenAPI Endpoint
Query the agent over HTTP on port `8642`:
```bash
curl -X POST "http://localhost:8642/v1/chat/completions" \
  -H "Authorization: Bearer sk-hermes-local-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "LExI",
    "messages": [
      {"role": "user", "content": "What tools and skills do you have available?"}
    ]
  }'
```

---

## 📂 Configuration & Persistent State

When deployed with `lexi-core`, agent state is mounted in `./data/hermes/`:

| Path | Purpose |
|---|---|
| `SOUL.md` | Core persona, behavioral rules, and root system prompt |
| `config.yaml` | Model endpoints (vLLM), tool configurations, and API settings |
| `memory.md` | Agent long-term notes and facts remembered across sessions |
| `user.md` | User profile, preferences, and environment facts |
| `skills/` | Custom procedural skill directories (`SKILL.md`) |
| `state.db` | SQLite database storing conversation history and session indexes |

---

## 📄 License

MIT — see [LICENSE](LICENSE). Forked from Nous Research.
