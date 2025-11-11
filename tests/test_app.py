from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_mcp_simple():
    r = client.post("/mcp", json={"text": "What is 1 + 2?"})
    assert r.status_code == 200
    assert r.json().get("result") == "3"


def test_mcp_nlp():
    r = client.post("/mcp", json={"text": "Calculate 2 times 3 plus 4"})
    assert r.status_code == 200
    assert r.json().get("result") == "10"
