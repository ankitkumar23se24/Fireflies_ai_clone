def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/v1/health").status_code == 200


def test_create_manual_meeting(client):
    r = client.post("/api/v1/meetings", json={"title": "Manual", "participants": [{"name": "Ann"}], "duration_seconds": 600})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Manual" and body["participants"][0]["name"] == "Ann" and body["summary"] is None


def test_create_from_transcript_enriches(meeting):
    assert {p["name"] for p in meeting["participants"]} == {"Ankit", "Rahul"}
    assert meeting["summary"]["overview"]
    assert len(meeting["topics"]) >= 1 and len(meeting["chapters"]) >= 1
    assert meeting["duration_seconds"] > 0
    assert any("API spec" in a["title"] for a in meeting["action_items"])


def test_get_update_delete(client, meeting):
    mid = meeting["id"]
    assert client.get(f"/api/v1/meetings/{mid}").json()["title"] == "Architecture Sync"
    r = client.patch(f"/api/v1/meetings/{mid}", json={"title": "Renamed <b>x</b>", "tags": ["a", "b"]})
    assert r.status_code == 200 and r.json()["title"] == "Renamed x" and [t["name"] for t in r.json()["tags"]] == ["a", "b"]
    assert client.delete(f"/api/v1/meetings/{mid}").status_code == 204
    assert client.get(f"/api/v1/meetings/{mid}").status_code == 404
    assert client.get(f"/api/v1/meetings/{mid}/transcript").status_code == 404  # cascade removed


def test_list_filters_and_pagination(client, meeting):
    client.post("/api/v1/meetings", json={"title": "Other", "participants": [{"name": "Zed"}], "tags": ["misc"]})
    all_ = client.get("/api/v1/meetings").json()
    assert all_["total"] == 2
    assert client.get("/api/v1/meetings", params={"q": "architecture"}).json()["total"] == 1
    assert client.get("/api/v1/meetings", params={"q": "FastAPI"}).json()["total"] == 1  # transcript text
    assert client.get("/api/v1/meetings", params={"q": "zed"}).json()["total"] == 1  # participant
    assert client.get("/api/v1/meetings", params={"participant": "Rahul"}).json()["total"] == 1
    assert client.get("/api/v1/meetings", params={"tag": "MISC"}).json()["total"] == 1
    assert client.get("/api/v1/meetings", params={"page_size": 1}).json()["items"].__len__() == 1
    oldest = client.get("/api/v1/meetings", params={"sort": "oldest"}).json()["items"]
    assert oldest[0]["id"] <= oldest[1]["id"]
    opts = client.get("/api/v1/meetings/filters").json()
    assert "Zed" in opts["participants"] and "eng" in opts["tags"]


def test_invalid_input_and_404(client):
    r = client.post("/api/v1/meetings", json={"title": ""})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert client.post("/api/v1/meetings", json={"title": "x", "transcript_text": "no speakers here"}).status_code == 422
    assert client.get("/api/v1/meetings/9999").status_code == 404
    assert client.get("/api/v1/meetings/abc").status_code == 422
    assert client.patch("/api/v1/meetings/9999", json={"title": "x"}).status_code == 404
    err = client.get("/api/v1/meetings/9999").json()["error"]
    assert err["code"] == "not_found" and err["request_id"]
    assert client.get("/api/v1/nope").status_code == 404


def test_import_file_upload(client):
    vtt = b"WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Ann>Hello everyone, we need to ship by Friday.</v>\n"
    r = client.post("/api/v1/meetings/import", files={"file": ("standup.vtt", vtt)}, data={"title": "VTT meeting"})
    assert r.status_code == 201 and r.json()["participants"][0]["name"] == "Ann"
    js = b'{"title":"From JSON","segments":[{"speaker":"Bo","start":0,"end":5,"text":"Hi all"}]}'
    r = client.post("/api/v1/meetings/import", files={"file": ("t.json", js)})
    assert r.status_code == 201 and r.json()["title"] == "From JSON"
    bad = client.post("/api/v1/meetings/import", files={"file": ("x.exe", b"abc")})
    assert bad.status_code == 422
    assert client.post("/api/v1/meetings/import", files={"file": ("bad.json", b"{oops")}).status_code == 422
    big = b"A: " + b"x" * (3 * 1024 * 1024)
    assert client.post("/api/v1/meetings/import", files={"file": ("big.txt", big)}).status_code == 413


def test_export_formats(client, meeting):
    mid = meeting["id"]
    md = client.get(f"/api/v1/meetings/{mid}/export", params={"format": "markdown"})
    assert md.status_code == 200 and "## Transcript" in md.text and "## Action Items" in md.text and "attachment" in md.headers["content-disposition"]
    txt = client.get(f"/api/v1/meetings/{mid}/export", params={"format": "txt", "scope": "transcript"})
    assert "[00:08] Rahul:" in txt.text and "Action Items" not in txt.text
    assert client.get(f"/api/v1/meetings/{mid}/export", params={"format": "pdf"}).status_code == 422


def test_analytics_and_ai(client, meeting):
    mid = meeting["id"]
    ov = client.get("/api/v1/analytics/overview").json()
    assert ov["total_meetings"] == 1 and len(ov["meetings_per_week"]) == 8
    ma = client.get(f"/api/v1/meetings/{mid}/analytics").json()
    assert {s["speaker"] for s in ma["speakers"]} == {"Ankit", "Rahul"}
    ans = client.post(f"/api/v1/meetings/{mid}/ask", json={"question": "Which database did we decide on?"}).json()
    assert "SQLite" in ans["answer"] and ans["citations"]
    assert client.post(f"/api/v1/meetings/{mid}/ask", json={"question": "x"}).status_code == 422
    assert client.post(f"/api/v1/meetings/{mid}/generate-summary").status_code == 200
