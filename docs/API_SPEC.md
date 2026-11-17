# API_SPEC.md — REST & SSE 接口契约（唯一真相源）

所有接口统一前缀 `/api/v1`。除 `/health` 与 `/auth/dev-login` 外，均需携带 `Authorization: Bearer <jwt>`。

## 1. 鉴权与会话

- `POST /auth/dev-login` -> `{username, role}` -> `{access_token, token_type, user}`
- `GET /auth/me` -> `AuthContext`
- `POST /sessions` -> `{agent_name, title}` -> `{id, user_id, ...}`
- `GET /sessions` -> `Session[]`
- `GET /sessions/{session_id}/messages` -> `Message[]`

## 2. 流式对话 (SSE)

- `POST /sessions/{session_id}/chat/stream` -> `{message}` -> `text/event-stream`
- **SSE 事件协议**：
  - `event: thought` -> `{"step": int, "status": "reasoning"}`
  - `event: tool_start` -> `{"tool": str, "args": dict}`
  - `event: citations` -> `{"items": [{index, title, source_path, heading_path, score, snippet}]}`
  - `event: tool_result` -> `{"tool": str, "duration_ms": int, "preview": str}`
  - `event: token` -> `{"text": str}`
  - `event: done` -> `{"run_id": uuid, "total_tokens": int, "latency_ms": int}`
  - `event: error` -> `{"message": str}`

## 3. 记忆、知识库、工具与评测

- `GET|POST /memories`, `DELETE /memories/{memory_id}`
- `POST /docs/ingest` -> `{title, source_path, category, content}` -> `{document_id, status, chunks}`
- `GET /docs`, `DELETE /docs/{doc_id}`, `POST /docs/search` -> `{query, category, top_k}`
- `GET /tools`（按 `AuthContext.allowed_tools` 裁剪）, `GET /runs/{run_id}/trace`
- `GET /eval/cases` -> `EvalCase[]`（读取 `eval/golden_qa.json`）
- `POST /eval/seed` -> 初始化示例文档到 Postgres
- `POST /eval/run` -> `{seed_if_empty, top_k}` -> `{summary: {total, passed, hit_rate_at_3, mrr, avg_latency_ms}, results}`
- `POST /docs/upload` -> `multipart/form-data` (`files[]`, `category`) -> 批量入库（支持 `.md/.txt/.pdf/.zip`）
- `POST /docs/search-debug` -> `{query, category, top_k, min_score}` -> `{tokens, rejected, latency_ms, vec_hits, fts_hits, reranked_hits}`
- `POST /auth/register` -> `{username, password, role, groups}` -> `{access_token, user}`
- `POST /auth/login` -> `{username, password}` -> `{access_token, user}`
- `kb_documents.allowed_groups` 与 `users.groups` 通过 PostgreSQL `&&` 数组重叠过滤文档可见性。
