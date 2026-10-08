def test_global_search_all_sources(client, meeting):
    client.post("/api/v1/meetings", json={"title": "FastAPI Workshop", "participants": [{"name": "Fabian"}]})
    hits = client.get("/api/v1/search", params={"q": "fastapi"}).json()
    types = {h["type"] for h in hits["hits"]}
    assert {"title", "transcript"} <= types
    t = next(h for h in hits["hits"] if h["type"] == "transcript")
    assert t["timestamp"] == 8.0 and t["segment_id"] and t["participant"] == "Rahul" and t["meeting_title"] == "Architecture Sync"
    assert "participant" in {h["type"] for h in client.get("/api/v1/search", params={"q": "fabian"}).json()["hits"]}
    assert "action_item" in {h["type"] for h in client.get("/api/v1/search", params={"q": "API spec"}).json()["hits"]}
    assert "topic" in {h["type"] for h in client.get("/api/v1/search", params={"q": client.get(f"/api/v1/meetings/{meeting['id']}").json()['topics'][0]['name'].split()[0]}).json()["hits"]}


def test_search_edge_cases(client, meeting):
    assert client.get("/api/v1/search", params={"q": ""}).json()["total"] == 0
    assert client.get("/api/v1/search", params={"q": "a"}).json()["total"] == 0
    assert client.get("/api/v1/search", params={"q": "%"}).json()["total"] == 0  # LIKE wildcards escaped
    assert client.get("/api/v1/search", params={"q": "x" * 500}).status_code == 422
    assert client.get("/api/v1/search", params={"q": "' OR 1=1 --"}).status_code == 200
