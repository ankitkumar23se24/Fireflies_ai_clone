import pytest

from app.core.exceptions import ValidationFailed
from app.services.transcript_parser import parse_transcript
from tests.conftest import TRANSCRIPT


def test_parse_txt_variants():
    segs, _ = parse_transcript("[00:02]\nAnkit:\nLet's go.\n\n[00:08]\nRahul:\nSure.")
    assert [(s.speaker, s.start_time) for s in segs] == [("Ankit", 2.0), ("Rahul", 8.0)]
    segs, _ = parse_transcript("Sam: hello there\nPriya: hi")
    assert segs[1].start_time >= segs[0].end_time
    segs, _ = parse_transcript("[01:02:03] Al: long meeting")
    assert segs[0].start_time == 3723


def test_parse_vtt_json_and_errors():
    segs, _ = parse_transcript("WEBVTT\n\n00:00:01.000 --> 00:00:03.500\nBob: ok then")
    assert segs[0].speaker == "Bob" and segs[0].end_time == 3.5
    segs, meta = parse_transcript('{"title":"T","segments":[{"speaker":"A","start":"00:05","text":"x"}]}')
    assert segs[0].start_time == 5 and meta["title"] == "T"
    for bad in ("", "just words no speaker", '[{"speaker":"A"}]', "{not json"):
        with pytest.raises(ValidationFailed):
            parse_transcript(bad, "json" if bad.startswith(("[", "{")) else "auto")


def test_get_transcript(client, meeting):
    t = client.get(f"/api/v1/meetings/{meeting['id']}/transcript").json()
    assert len(t["segments"]) == 4 and t["speakers"] == ["Ankit", "Rahul"]
    assert t["segments"][0]["speaker"] == "Ankit" and t["segments"][0]["start_time"] == 2.0


def test_import_replace_and_append(client, meeting):
    mid = meeting["id"]
    r = client.post(f"/api/v1/meetings/{mid}/transcript", json={"text": "Zoe: A brand new opening line.", "mode": "replace"})
    assert r.status_code == 201 and len(r.json()["segments"]) == 1
    r = client.post(f"/api/v1/meetings/{mid}/transcript", json={"text": "Zoe: Second.\nAl: Third.", "mode": "append"})
    segs = r.json()["segments"]
    assert [s["sequence_number"] for s in segs] == [1, 2, 3] and segs[1]["start_time"] > segs[0]["start_time"]
    assert client.post(f"/api/v1/meetings/{mid}/transcript", json={}).status_code == 422
    assert client.post("/api/v1/meetings/999/transcript", json={"text": "A: b"}).status_code == 404


def test_update_and_delete_segment(client, meeting):
    seg = client.get(f"/api/v1/meetings/{meeting['id']}/transcript").json()["segments"][0]
    r = client.patch(f"/api/v1/transcript/{seg['id']}", json={"text": "Edited text", "speaker": "Newcomer"})
    assert r.status_code == 200 and r.json()["text"] == "Edited text" and r.json()["speaker"] == "Newcomer"
    assert client.patch(f"/api/v1/transcript/{seg['id']}", json={"start_time": 500, "end_time": 1}).status_code == 422
    assert client.patch(f"/api/v1/transcript/{seg['id']}", json={"text": ""}).status_code == 422
    assert client.delete(f"/api/v1/transcript/{seg['id']}").status_code == 204
    assert client.delete(f"/api/v1/transcript/{seg['id']}").status_code == 404
    assert client.patch("/api/v1/transcript/9999", json={"text": "x"}).status_code == 404


def test_search_in_meeting(client, meeting):
    mid = meeting["id"]
    r = client.get(f"/api/v1/meetings/{mid}/search", params={"q": "fastapi"}).json()
    assert r["total"] == 1 and r["hits"][0]["participant"] == "Rahul" and r["hits"][0]["timestamp"] == 8.0
    assert client.get(f"/api/v1/meetings/{mid}/search", params={"q": "benchmark"}).json()["total"] == 1
    assert client.get(f"/api/v1/meetings/{mid}/search", params={"q": "zzzz"}).json()["total"] == 0
    assert client.get(f"/api/v1/meetings/{mid}/search", params={"q": '"; DROP TABLE meetings; --'}).status_code == 200
    assert client.get(f"/api/v1/meetings/{mid}/search").status_code == 422
    assert client.get("/api/v1/meetings/777/search", params={"q": "a"}).status_code == 404


def test_fts_edit_stays_in_sync(client, meeting):
    mid = meeting["id"]
    seg = client.get(f"/api/v1/meetings/{mid}/transcript").json()["segments"][0]
    client.patch(f"/api/v1/transcript/{seg['id']}", json={"text": "Completely unique zebra phrase"})
    assert client.get(f"/api/v1/meetings/{mid}/search", params={"q": "zebra"}).json()["total"] == 1
    assert client.get(f"/api/v1/meetings/{mid}/search", params={"q": "backend architecture"}).json()["total"] == 0


def test_comments_and_highlights(client, meeting):
    mid = meeting["id"]
    seg = client.get(f"/api/v1/meetings/{mid}/transcript").json()["segments"][1]
    c = client.post(f"/api/v1/meetings/{mid}/comments", json={"transcript_segment_id": seg["id"], "text": "Nice <script>x</script>point"})
    assert c.status_code == 201 and c.json()["text"] == "Nice xpoint"
    h = client.post(f"/api/v1/meetings/{mid}/highlights", json={"transcript_segment_id": seg["id"], "color": "green", "note": "key"})
    assert h.status_code == 201
    assert client.post(f"/api/v1/meetings/{mid}/highlights", json={"transcript_segment_id": seg["id"], "color": "neon"}).status_code == 422
    seg_out = client.get(f"/api/v1/meetings/{mid}/transcript").json()["segments"][1]
    assert len(seg_out["comments"]) == 1 and seg_out["highlights"][0]["color"] == "green"
    assert client.patch(f"/api/v1/highlights/{h.json()['id']}", json={"note": "updated"}).json()["note"] == "updated"
    assert len(client.get(f"/api/v1/meetings/{mid}/comments").json()) == 1
    assert client.delete(f"/api/v1/comments/{c.json()['id']}").status_code == 204
    assert client.delete(f"/api/v1/comments/{c.json()['id']}").status_code == 404
    assert client.delete(f"/api/v1/highlights/{h.json()['id']}").status_code == 204
    # segment of another meeting must be rejected
    other = client.post("/api/v1/meetings", json={"title": "Other"}).json()
    assert client.post(f"/api/v1/meetings/{other['id']}/comments", json={"transcript_segment_id": seg["id"], "text": "x"}).status_code == 404
