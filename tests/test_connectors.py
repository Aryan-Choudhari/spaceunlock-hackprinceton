import asyncio
import httpx
import pytest
from fastapi import HTTPException
from backend import connectors as c


def test_status_does_not_expose_credentials(monkeypatch):
    monkeypatch.setattr(
        c,
        "config",
        lambda: {
            "MATTERPORT_API_KEY": "secret-key",
            "MATTERPORT_API_TOKEN": "secret-token",
            "VEXCEL_API_KEY": "secret-vexcel",
        },
    )
    monkeypatch.setattr(c, "selection", lambda: None)
    result = c.status()
    assert "secret" not in str(result)
    assert result["agent"]["status"] == "deterministic_fallback"


def test_missing_credentials(monkeypatch):
    monkeypatch.setattr(c, "config", lambda: {})
    with pytest.raises(HTTPException) as ex:
        asyncio.run(c.graph("{models{totalResults}}"))
    assert ex.value.status_code == 503


def test_selected_model_is_verified_before_save(monkeypatch, tmp_path):
    monkeypatch.setattr(c, "PRIVATE", tmp_path)

    async def fake_model(id):
        return {"source": "Matterport Model API", "data": {"id": id, "name": "Test"}}

    monkeypatch.setattr(c, "model", fake_model)
    asyncio.run(c.select(c.Select(model_id="test-id")))
    assert c.selection()["data"]["id"] == "test-id"
    assert (tmp_path / "selected-model.json").stat().st_mode & 0o777 == 0o600


def test_invalid_model_id():
    with pytest.raises(HTTPException) as ex:
        asyncio.run(c.model("../bad"))
    assert ex.value.status_code == 422


def test_graph_errors_sanitized(monkeypatch):
    monkeypatch.setattr(
        c,
        "config",
        lambda: {"MATTERPORT_API_KEY": "secret", "MATTERPORT_API_TOKEN": "secret"},
    )

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            return httpx.Response(
                200, json={"errors": [{"message": "secret upstream details"}]}
            )

    monkeypatch.setattr(c.httpx, "AsyncClient", FakeClient)
    with pytest.raises(HTTPException) as ex:
        asyncio.run(c.graph("query"))
    assert "secret" not in ex.value.detail
