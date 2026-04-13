from app.integrations.notion_client import NotionClient


def test_create_database_page_delegates_request(monkeypatch) -> None:
    captured: dict = {}

    def _mock_request(self, method: str, path: str, payload: dict):
        captured["method"] = method
        captured["path"] = path
        captured["payload"] = payload
        return {"id": "page-db-123"}

    monkeypatch.setattr(NotionClient, "_request", _mock_request)

    response = NotionClient().create_database_page(
        database_id="db-123",
        properties={"Name": {"title": [{"type": "text", "text": {"content": "Test"}}]}},
        children=[],
    )

    assert response["id"] == "page-db-123"
    assert captured["method"] == "POST"
    assert captured["path"] == "/pages"
    assert captured["payload"]["parent"]["database_id"] == "db-123"


def test_create_child_page_delegates_request(monkeypatch) -> None:
    captured: dict = {}

    def _mock_request(self, method: str, path: str, payload: dict):
        captured["method"] = method
        captured["path"] = path
        captured["payload"] = payload
        return {"id": "page-child-123"}

    monkeypatch.setattr(NotionClient, "_request", _mock_request)

    response = NotionClient().create_child_page(
        parent_page_id="parent-123",
        title="Child Page",
        children=[],
    )

    assert response["id"] == "page-child-123"
    assert captured["method"] == "POST"
    assert captured["path"] == "/pages"
    assert captured["payload"]["parent"]["page_id"] == "parent-123"