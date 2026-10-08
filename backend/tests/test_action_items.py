def test_action_item_crud(client, meeting):
    mid = meeting["id"]
    base = len(client.get(f"/api/v1/meetings/{mid}/action-items").json())
    r = client.post(f"/api/v1/meetings/{mid}/action-items", json={"title": "Write docs", "assignee": "Ankit", "due_date": "2030-01-31"})
    assert r.status_code == 201
    item = r.json()
    assert item["status"] == "TODO" and item["due_date"] == "2030-01-31"
    r = client.patch(f"/api/v1/action-items/{item['id']}", json={"status": "DONE", "description": "all of it"})
    assert r.json()["status"] == "DONE" and r.json()["description"] == "all of it"
    done = client.get(f"/api/v1/meetings/{mid}/action-items", params={"status": "DONE"}).json()
    assert [i["id"] for i in done] == [item["id"]]
    mine = client.get(f"/api/v1/meetings/{mid}/action-items", params={"assignee": "Ankit"}).json()
    assert any(i["id"] == item["id"] for i in mine)
    assert client.delete(f"/api/v1/action-items/{item['id']}").status_code == 204
    assert len(client.get(f"/api/v1/meetings/{mid}/action-items").json()) == base


def test_action_item_validation_and_404(client, meeting):
    mid = meeting["id"]
    assert client.post(f"/api/v1/meetings/{mid}/action-items", json={"title": ""}).status_code == 422
    assert client.post(f"/api/v1/meetings/{mid}/action-items", json={"title": "x", "status": "NOPE"}).status_code == 422
    assert client.post(f"/api/v1/meetings/{mid}/action-items", json={"title": "x", "due_date": "not-a-date"}).status_code == 422
    assert client.post("/api/v1/meetings/999/action-items", json={"title": "x"}).status_code == 404
    assert client.patch("/api/v1/action-items/999", json={"status": "DONE"}).status_code == 404
    assert client.delete("/api/v1/action-items/999").status_code == 404
    assert client.get(f"/api/v1/meetings/{mid}/action-items", params={"status": "BAD"}).status_code == 422
