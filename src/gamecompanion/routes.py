from __future__ import annotations

import io
import json
import os
import zipfile
from starlette.responses import JSONResponse, StreamingResponse
from starlette.requests import Request
from starlette.datastructures import UploadFile

from gamecompanion.main import (
    TEST_MODE,
    DATA_DIR,
    CONFIG_PATH,
    app,
    rt,
    _load_config,
    _save_config,
    _validate_api_key,
    _settings_page,
    _create_playthrough_page,
    _chat_page,
    _get_db,
    _welcome_page,
    _welcome_message_text,
    _is_offline,
    _build_rag_context,
    _load_stable_context,
    _maybe_handle_memory_query,
    _mock_llm_respond,
    _build_system_prompt,
    _STRUCTURED_OUTPUT_INSTRUCTIONS,
    _call_llm,
    _parse_llm_response,
    _strip_json_blobs,
    _mock_tavily_search,
    _call_tavily_search,
    _format_search_results,
    _SEARCH_CITATION_INSTRUCTIONS,
    _apply_context_deltas,
    _append_changelog,
    _summarize_context_deltas,
    _format_api_error,
    _rag_index_message,
    _upsert_node,
    _add_edge,
)


@rt("/")
def get():
    cfg = _load_config()
    if not cfg.get("api_key"):
        return _welcome_page()
    db = _get_db()
    row = db.execute("SELECT id FROM playthroughs ORDER BY updated_at DESC, id DESC LIMIT 1").fetchone()
    db.close()
    if not row:
        return _create_playthrough_page()
    return _chat_page(row["id"])


@rt("/api/test-key")
def post(api_key: str):
    valid, msg = _validate_api_key(api_key)
    if valid:
        from fasthtml.common import Span
        return Span(f"✓ {msg}", data_testid="api-key-status", style="color: #4caf50;")
    from fasthtml.common import Span
    return Span(f"✗ {msg}", data_testid="api-key-status", style="color: #f44336;")


@rt("/setup/save-key")
def post(api_key: str, tavily_api_key: str = ""):
    cfg = _load_config()
    cfg["api_key"] = api_key
    if tavily_api_key:
        cfg["tavily_api_key"] = tavily_api_key
    _save_config(cfg)
    from starlette.responses import RedirectResponse
    return RedirectResponse("/setup/new-playthrough", status_code=303)


@rt("/settings")
def get(saved: int = 0):
    return _settings_page(saved)


@rt("/settings/save")
def post(api_key: str = "", tavily_api_key: str = "", debug_mode: str = "", model_name: str = ""):
    cfg = _load_config()
    if api_key:
        cfg["api_key"] = api_key
    if tavily_api_key:
        cfg["tavily_api_key"] = tavily_api_key
    if model_name:
        cfg["model_name"] = model_name
    cfg["debug_mode"] = bool(debug_mode)
    _save_config(cfg)
    from starlette.responses import RedirectResponse
    return RedirectResponse("/settings?saved=1", status_code=303)


@rt("/setup/new-playthrough")
def get():
    return _create_playthrough_page()


@rt("/playthrough/create")
def post(name: str, game_title: str = ""):
    db = _get_db()
    cur = db.execute("INSERT INTO playthroughs (name, game_title) VALUES (?, ?)", (name, game_title))
    db.commit()
    pid = cur.lastrowid
    welcome_text = _welcome_message_text(game_title)
    db.execute("INSERT INTO messages (playthrough_id, role, content) VALUES (?, 'assistant', ?)", (pid, welcome_text))
    db.commit()
    db.close()
    from starlette.responses import RedirectResponse
    return RedirectResponse(f"/chat/{pid}", status_code=303)


@rt("/chat/{playthrough_id}")
def get(playthrough_id: int):
    return _chat_page(playthrough_id)


@rt("/chat/{playthrough_id}/send")
def post(playthrough_id: int, message: str):
    db = _get_db()
    cfg = _load_config()
    offline_reply = None
    if _is_offline(cfg):
        offline_reply = "⚠️ You're offline. Connect to the internet to continue chatting."

    cur = db.execute("INSERT INTO messages (playthrough_id, role, content) VALUES (?, 'user', ?)", (playthrough_id, message))
    db.commit()
    user_msg_id = cur.lastrowid

    pt = db.execute("SELECT name, game_title FROM playthroughs WHERE id = ?", (playthrough_id,)).fetchone()
    rag_context = _build_rag_context(db, playthrough_id, message)
    stable_context = _load_stable_context(db, playthrough_id)
    memory_reply = _maybe_handle_memory_query(message, stable_context)
    if offline_reply:
        memory_reply = offline_reply

    try:
        deltas = []
        if memory_reply is not None:
            ai_text = memory_reply
            raw_response = None
        elif TEST_MODE:
            if cfg.get("force_api_error"):
                raise RuntimeError(str(cfg.get("force_api_error")))
            raw_response = _mock_llm_respond(message, rag_context, stable_context=stable_context)
        else:
            past_msgs = db.execute("SELECT role, content FROM messages WHERE playthrough_id = ? ORDER BY created_at", (playthrough_id,)).fetchall()
            history = []
            for m in past_msgs:
                if m["role"] == "user" and m["content"] == message and m is past_msgs[-1]:
                    continue
                history.append({"role": "user" if m["role"] == "user" else "assistant", "parts": [m["content"]]})

            system_prompt = _build_system_prompt(pt["name"] if pt else "", pt["game_title"] if pt else "")
            system_prompt += "\n\n" + json.dumps(stable_context, ensure_ascii=False, indent=2)
            if rag_context:
                system_prompt += "\n\nRelevant prior context:\n" + rag_context
            system_prompt += _STRUCTURED_OUTPUT_INSTRUCTIONS
            api_key = cfg.get("api_key", "")
            model_name = cfg.get("model_name", "gpt-4o")
            raw_response = _call_llm(api_key, system_prompt, history, message, model_name=model_name)

        if raw_response is not None:
            parsed = _parse_llm_response(raw_response)
            ai_text = _strip_json_blobs(parsed["response"])
            deltas = parsed.get("context_deltas", []) or []
            web_search = parsed.get("web_search")
            if not ai_text.strip():
                ai_text = "Got it — I've updated my notes."
        else:
            web_search = None

        search_unavailable = False
        if web_search and isinstance(web_search, dict) and web_search.get("query"):
            if TEST_MODE:
                search_results = _mock_tavily_search(web_search["query"])
            else:
                tavily_key = cfg.get("tavily_api_key", os.environ.get("TAVILY_API_KEY", ""))
                if tavily_key:
                    search_results = _call_tavily_search(tavily_key, web_search["query"])
                    if search_results is None:
                        search_results = []
                        search_unavailable = True
                else:
                    search_results = []
                    search_unavailable = True

            if search_results:
                search_context = _format_search_results(search_results)
                if TEST_MODE:
                    raw_response2 = _mock_llm_respond(message, rag_context, search_results=search_context, stable_context=stable_context)
                else:
                    raw_response2 = _call_llm(api_key, system_prompt + _SEARCH_CITATION_INSTRUCTIONS + "\n" + search_context, history, message, model_name=model_name)
                parsed2 = _parse_llm_response(raw_response2)
                ai_text = parsed2["response"]
                deltas = parsed2.get("context_deltas", []) or []
            elif search_unavailable:
                ai_text = "Web search is unavailable — add a Tavily API key in Settings."

        applied = 0
        if deltas:
            applied = _apply_context_deltas(db, playthrough_id, deltas)
            if applied > 0 and _load_config().get("debug_mode"):
                _append_changelog(playthrough_id, deltas)
        if applied > 0:
            summary, _ = _summarize_context_deltas(deltas)
            ai_text = f"{ai_text}\n\n📌 {summary}"

    except Exception as exc:
        ai_text = _format_api_error(exc)

    cur = db.execute("INSERT INTO messages (playthrough_id, role, content) VALUES (?, 'assistant', ?)", (playthrough_id, ai_text))
    ai_msg_id = cur.lastrowid
    _rag_index_message(db, playthrough_id, user_msg_id, "user", message)
    _rag_index_message(db, playthrough_id, ai_msg_id, "assistant", ai_text)
    db.execute("UPDATE playthroughs SET updated_at = datetime('now') WHERE id = ?", (playthrough_id,))
    db.commit()

    msgs = db.execute("SELECT * FROM messages WHERE playthrough_id = ? ORDER BY created_at", (playthrough_id,)).fetchall()
    db.close()

    from fasthtml.common import Div
    from gamecompanion.main import _render_ai_message
    els = []
    for m in msgs:
        if m["role"] == "user":
            els.append(Div(m["content"], cls="msg-user", data_testid="user-message"))
        else:
            els.append(Div(_render_ai_message(m["content"]), cls="msg-ai", data_testid="ai-message"))
    return tuple(els)


@rt("/playthrough/{playthrough_id}/rename")
def post(playthrough_id: int, name: str, game_title: str = ""):
    db = _get_db()
    db.execute("UPDATE playthroughs SET name = ?, game_title = ?, updated_at = datetime('now') WHERE id = ?", (name, game_title, playthrough_id))
    db.commit()
    db.close()
    from starlette.responses import RedirectResponse
    return RedirectResponse(f"/chat/{playthrough_id}", status_code=303)


@rt("/playthrough/{playthrough_id}/delete")
def get(playthrough_id: int):
    db = _get_db()
    db.execute("DELETE FROM graph_edges WHERE playthrough_id = ?", (playthrough_id,))
    db.execute("DELETE FROM graph_nodes WHERE playthrough_id = ?", (playthrough_id,))
    db.execute("DELETE FROM rag_chunks WHERE playthrough_id = ?", (playthrough_id,))
    db.execute("DELETE FROM messages WHERE playthrough_id = ?", (playthrough_id,))
    db.execute("DELETE FROM playthroughs WHERE id = ?", (playthrough_id,))
    db.commit()
    remaining = db.execute("SELECT id FROM playthroughs ORDER BY updated_at DESC, id DESC LIMIT 1").fetchone()
    db.close()
    from starlette.responses import RedirectResponse
    if remaining:
        return RedirectResponse(f"/chat/{remaining['id']}", status_code=303)
    return RedirectResponse("/setup/new-playthrough", status_code=303)


@rt("/playthrough/export")
def get(playthrough_id: int):
    db = _get_db()
    pt = db.execute("SELECT id, name, game_title, created_at, updated_at FROM playthroughs WHERE id = ?", (playthrough_id,)).fetchone()
    msgs = db.execute("SELECT role, content, created_at FROM messages WHERE playthrough_id = ? ORDER BY created_at", (playthrough_id,)).fetchall()
    stable_context = _load_stable_context(db, playthrough_id)
    db.close()

    payload = {"playthrough": dict(pt) if pt else {}, "messages": [dict(m) for m in msgs], "stable_context": stable_context}
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("playthrough.json", json.dumps(payload["playthrough"]))
        zf.writestr("messages.json", json.dumps(payload["messages"]))
        zf.writestr("stable_context.json", json.dumps(payload["stable_context"]))
    mem.seek(0)
    return StreamingResponse(mem, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=playthrough_{playthrough_id}.zip"})


@rt("/playthrough/import")
def post(import_file: UploadFile):
    data = import_file.file.read()
    mem = io.BytesIO(data)
    with zipfile.ZipFile(mem, "r") as zf:
        playthrough = json.loads(zf.read("playthrough.json"))
        messages = json.loads(zf.read("messages.json"))
        stable_context = json.loads(zf.read("stable_context.json"))

    db = _get_db()
    name = playthrough.get("name", "Imported Playthrough")
    game_title = playthrough.get("game_title", "")
    existing = db.execute("SELECT id FROM playthroughs WHERE name = ?", (name,)).fetchone()
    if existing:
        name = f"{name} (Imported)"
    cur = db.execute("INSERT INTO playthroughs (name, game_title) VALUES (?, ?)", (name, game_title))
    db.commit()
    playthrough_id = cur.lastrowid

    for node in stable_context.get("nodes", []) or []:
        _upsert_node(db, playthrough_id, node["name"], node["kind"], node.get("properties", {}), node.get("status", "active"))
    for edge in stable_context.get("edges", []) or []:
        _add_edge(db, playthrough_id, edge["source"], edge["target"], edge["label"], edge.get("properties", {}))

    for m in messages:
        cur = db.execute("INSERT INTO messages (playthrough_id, role, content) VALUES (?, ?, ?)", (playthrough_id, m.get("role", "user"), m.get("content", "")))
        msg_id = cur.lastrowid
        _rag_index_message(db, playthrough_id, msg_id, m.get("role", "user"), m.get("content", ""))
    db.commit()
    db.close()
    from starlette.responses import RedirectResponse
    return RedirectResponse(f"/chat/{playthrough_id}", status_code=303)


if TEST_MODE:
    @rt("/test/reset")
    def post():
        db = _get_db()
        db.execute("DELETE FROM graph_edges")
        db.execute("DELETE FROM graph_nodes")
        db.execute("DELETE FROM rag_chunks")
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM playthroughs")
        db.commit()
        db.close()
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()
        return "ok"

    @rt("/test/inject-messages")
    def post(playthrough_id: int, messages: str):
        db = _get_db()
        msg_list = json.loads(messages)
        for msg in msg_list:
            cur = db.execute("INSERT INTO messages (playthrough_id, role, content) VALUES (?, ?, ?)", (playthrough_id, msg["role"], msg["content"]))
            msg_id = cur.lastrowid
            _rag_index_message(db, playthrough_id, msg_id, msg["role"], msg["content"])
        db.commit()
        db.close()
        return f"ok: injected {len(msg_list)} messages"

    @rt("/test/set-config")
    async def post(request: Request):
        body = await request.body()
        data = json.loads(body.decode("utf-8") or "{}")
        cfg = _load_config()
        cfg.update(data)
        _save_config(cfg)
        return JSONResponse({"ok": True})

    @rt("/test/changelog")
    def get():
        path = DATA_DIR / "changelog.jsonl"
        if not path.exists():
            return JSONResponse({"lines": []})
        lines = path.read_text(encoding="utf-8").splitlines()
        return JSONResponse({"lines": lines})

    @rt("/test/get-config")
    def get():
        return JSONResponse(_load_config())

    @rt("/test/rag-stats")
    def get(playthrough_id: int):
        db = _get_db()
        row = db.execute("SELECT COUNT(*) as c FROM rag_chunks WHERE playthrough_id = ?", (playthrough_id,)).fetchone()
        db.close()
        return JSONResponse({"indexed_count": row["c"]})
