"""FastAPI 接口冒烟测试：覆盖鉴权、工具权限裁剪、记忆 CRUD、知识库与评测接口。"""

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import httpx

from src.api.deps import (
    create_access_token,
    get_doc_repo,
    get_memory_repo,
    get_rag_service,
)
from src.main import app
from src.schemas.models import AuthContext
from src.services.embedding_service import EmbeddingService
from src.services.rag_service import RagService
from tests.test_rag_pipeline import FakeDocRepo


class FakeMemoryRepo:
    def __init__(self) -> None:
        self.items: list[dict] = []

    async def create_memory(self, user_id: UUID, memory_type: str, content: str, importance: int = 3):
        row = {"id": str(uuid4()), "user_id": user_id, "memory_type": memory_type, "content": content, "importance": importance}
        self.items.append(row)
        return row

    async def list_memories(self, user_id: UUID, limit: int = 20):
        return [m for m in self.items if m["user_id"] == user_id][:limit]


def test_api_auth_tools_memory_and_rag_endpoints() -> None:
    fake_doc_repo = FakeDocRepo()
    fake_mem_repo = FakeMemoryRepo()

    async def override_rag() -> RagService:
        return RagService(doc_repo=fake_doc_repo, embed_service=EmbeddingService(httpx.AsyncClient()))  # type: ignore[arg-type]

    app.dependency_overrides[get_doc_repo] = lambda: fake_doc_repo
    app.dependency_overrides[get_memory_repo] = lambda: fake_mem_repo
    app.dependency_overrides[get_rag_service] = override_rag

    try:
        client = TestClient(app, raise_server_exceptions=False)
        assert client.get("/health").status_code == 200
        assert client.post("/api/v1/docs/search", json={"query": "pgvector"}).status_code == 401

        # 测试普通角色仅能看见 rag_search 工具（权限裁剪）
        user_token = create_access_token(
            AuthContext(user_id=uuid4(), username="readonly_u", role="readonly", allowed_tools=["rag_search"])
        )
        tools_resp = client.get("/api/v1/tools", headers={"Authorization": f"Bearer {user_token}"})
        assert tools_resp.status_code == 200
        assert [t["function"]["name"] for t in tools_resp.json()] == ["rag_search"]

        # 测试管理员全流程：记忆写入 -> 知识库入库 -> 检索 -> 拉取黄金测试集
        admin_token = create_access_token(
            AuthContext(user_id=uuid4(), username="admin_u", role="admin", allowed_tools=["rag_search", "memory_save"])
        )
        headers = {"Authorization": f"Bearer {admin_token}"}
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

        mem_resp = client.post(
            "/api/v1/memories",
            headers=headers,
            json={"memory_type": "fact", "content": "使用 Postgres 17", "importance": 5},
        )
        assert mem_resp.status_code == 200
        assert len(client.get("/api/v1/memories", headers=headers).json()) == 1

        ingest_resp = client.post(
            "/api/v1/docs/ingest",
            headers=headers,
            json={
                "title": "架构说明",
                "source_path": "docs/arch.md",
                "category": "arch",
                "content": "# 架构\n\n## RAG 服务\nRAG 作为 Services 层的一部分挂载给 AgentLoop。",
            },
        )
        assert ingest_resp.status_code == 200 and ingest_resp.json()["status"] == "indexed"

        search_resp = client.post(
            "/api/v1/docs/search",
            headers=headers,
            json={"query": "AgentLoop RAG", "category": "arch", "top_k": 2},
        )
        assert search_resp.status_code == 200 and len(search_resp.json()["hits"]) == 1

        eval_cases = client.get("/api/v1/eval/cases", headers=headers)
        assert eval_cases.status_code == 200 and len(eval_cases.json()) >= 6
    finally:
        app.dependency_overrides.clear()
