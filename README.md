# CodeGen – Interactive Coding Agent

CodeGen is an interactive AI coding agent powered by Google GenAI (Gemini) with tool-use, persistent conversational memory, and a safe sandbox for file operations. It supports both continuous interactive sessions and single-shot commands, and provides a structured planning mode powered by Instructor + Pydantic models.

## Features at a Glance

- Interactive REPL-like session: run once and chat continuously
- Tool calling with a sandboxed working directory `code-files/`
- Safe file operations: read, write, run Python files, list files, delete (safe/permanent), search memory
- Conversation memory persisted in `db/memory.json`
- Structured planning mode (no execution) via Instructor + Pydantic
- Clear deletion UX: safe delete to `.trash` or permanent delete

## Quickstart

1. Install dependencies (uv recommended):

```bash
uv sync
```

2. Set your API key in a `.env` file:

```bash
echo "GEMINI_API_KEY=YOUR_KEY_HERE" > .env
```

3. Start interactive session:

```bash
uv run main.py
```

- Type your prompts directly.
- Exit with `exit` or Ctrl+C.

4. Single-shot mode (backward compatible):

```bash
uv run main.py "create a fizzbuzz program"
```

5. Structured planning mode (no tool execution):

```bash
uv run main.py "create a fizzbuzz program" --structured
```

This returns formatted JSON (goal, steps, tool_calls) using Pydantic models via Instructor.

## Working Directory (Sandbox)

All file operations are restricted to `code-files/`. The agent will not operate outside this directory.

## Tools in `functions/`

- `get_files_info`

  - List files and directories within `code-files/` with basic metadata.

- `read`

  - Read file content (truncated by `MAX_CHARS` in `config.py`).

- `write`

  - Create or update files. Enforces `MAX_WRITE_CHARS` from `config.py`.

- `run_python`

  - Execute a Python file inside the sandbox with optional arguments.
  - Limits enforced by `MAX_RUN_ARGS` and `MAX_ARG_LEN` in `config.py`.

- `delete`

  - Two modes:
    - Safe delete (default): moves the file to `code-files/.trash/` so it can be recovered
    - Permanent delete: removes the file/directory irreversibly (`os.remove`/`shutil.rmtree`)
  - The agent first checks existence, then prompts you to choose: safe, permanent, or cancel.

- `search_memory`

  - Search past Q&A pairs stored in `db/memory.json` and return relevant entries.

- `structured.py`
  - Defines Pydantic models for structured output:
    - `Plan { goal: str, steps: [Step], tool_calls: [ToolCall] }`
    - `Step { action: str, reason: str }`
    - `ToolCall { tool: str }` (tool is an exact function name: `get_files_info`, `read`, `write`, `run_python`, `delete`, `search_memory`)

## How Calls Are Routed (`call_function.py`)

Model function calls are dispatched to the corresponding tool implementation while enforcing the sandbox path:

```python
# call_function.py
if function_call_part.name == "write":
    result = write(working_directory, **function_call_part.args)
# ... similarly for read, delete, run_python, get_files_info, search_memory
```

## Memory: `db/memory.json`

- Stores an append-only log of Q&A pairs used for lightweight context and follow-up handling.
- In `main.py`, the last 5 entries are summarized and provided to the model as recent context.
- `search_memory` can retrieve relevant Q&A entries based on a query.

## Deletion UX (Safe vs Permanent)

- The agent first checks whether the file exists.
- If it exists, you are asked:
  - "Do you wish to safe delete or permanently delete [file_path]? Safe delete moves your file to a trash folder from where you can recover your file if needed. Reply with 'safe' for safe delete, 'permanent' for permanent delete, or 'cancel' to abort."
- Safe delete moves files into `code-files/.trash/` (with collision-safe naming).
- Permanent delete removes files or folders immediately.

## Structured Planning Mode (Instructor + Pydantic)

- Use `--structured` (or `-s`) to request a plan without executing tools.
- The agent returns JSON with:

```json
{
  "goal": "...",
  "steps": [{ "action": "...", "reason": "..." }],
  "tool_calls": [{ "tool": "write" }, { "tool": "run_python" }]
}
```

- Backed by `functions/structured.py` Pydantic models and `instructor` integration.

## Limits & Safety (config.py)

- `MAX_CHARS`: max characters read by `read`
- `MAX_WRITE_CHARS`: max content size for `write`
- `MAX_RUN_ARGS`: max number of args for `run_python`
- `MAX_ARG_LEN`: max length of any single arg passed to `run_python`

## Usage Examples

- Interactive session:

```bash
uv run main.py
# 💬 You: list files
# 💬 You: create a file hello.py with print("hi")
# 💬 You: run hello.py
# 💬 You: delete hello.py  # choose safe or permanent
```

- Single-shot:

```bash
uv run main.py "create fizzbuzz.py and run it"
```

- Structured planning (no execution):

```bash
uv run main.py "create a web scraper" --structured
```

## Improvements

- Replace JSON file memory with a vector database (e.g., Chroma, Qdrant) for semantic retrieval
- Support Postgres for durable, queryable memory storage
