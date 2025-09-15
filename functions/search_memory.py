import json
import os
from typing import List, Dict
from google.genai import types


MEMORY_FILE = "db/memory.json"


def _read_memory() -> List[Dict]:
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_memory(entries: List[Dict]) -> None:
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    tmp = MEMORY_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    os.replace(tmp, MEMORY_FILE)


def save_qa(user: str, assistant: str) -> str:
    entries = _read_memory()
    next_id = (entries[-1]["id"] + 1) if entries else 1
    record = {"id": next_id, "user": user, "assistant": assistant}
    entries.append(record)
    try:
        _write_memory(entries)
        return "ok"
    except Exception as e:
        return f"error: {e}"


def _tokens(text: str) -> List[str]:
    out = []
    buf = []
    for ch in text.lower():
        if ch.isalnum():
            buf.append(ch)
        else:
            if buf:
                out.append("".join(buf))
                buf = []
    if buf:
        out.append("".join(buf))
    return out


def _score(query: str, text: str) -> float:
    q = " ".join(_tokens(query))
    t = " ".join(_tokens(text))
    if not q or not t:
        return 0.0
    # Boost substring matches
    if q in t:
        return 2.0
    qset = set(q.split())
    tset = set(t.split())
    inter = len(qset & tset)
    if inter == 0:
        return 0.0
    return inter / max(1, len(qset))


def search_memory(query: str, top_k: int = 5) -> str:
    entries = _read_memory()
    if not entries:
        return json.dumps({"results": []})

    normalized = query.strip().lower()
    if "previous question" in normalized or "last question" in normalized:
        last = entries[-1]
        return json.dumps({"results": [last]})
    if "last fix" in normalized or "previous fix" in normalized or "what fix" in normalized:
        # naive: return last assistant message
        last = entries[-1]
        return json.dumps({"results": [last]})

    scored = []
    for rec in entries:
        text = f"{rec.get('user','')}\n{rec.get('assistant','')}"
        scored.append(( _score(query, text), rec ))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [r for s, r in scored[: max(1, top_k)] if s > 0.0]
    return json.dumps({"results": top}, ensure_ascii=False)


schema_search_memory = types.FunctionDeclaration(
    name="search_memory",
    description="Search conversation memory in memory.json and return the most relevant Q&A pairs.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "query": types.Schema(type=types.Type.STRING, description="The search query text"),
            "top_k": types.Schema(type=types.Type.INTEGER, description="Top results to return"),
        },
    ),
)


