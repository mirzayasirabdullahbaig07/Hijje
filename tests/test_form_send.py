"""The form sends its answers to the endpoint, in the format load_responses reads."""
import csv
import json
from pathlib import Path

import pytest

from hijje import collect

SENTENCES = str(Path(__file__).resolve().parent / "fixtures" / "sentences_fixture.tsv")
ENDPOINT = "https://script.example.test/exec"


def test_endpoint_must_be_https(tmp_path):
    with pytest.raises(ValueError):
        collect.make_form(SENTENCES, ["s00001"], tmp_path / "f.html", endpoint="http://x.test")


def test_no_endpoint_means_no_sending(tmp_path):
    collect.make_form(SENTENCES, ["s00001"], tmp_path / "f.html")
    assert '"endpoint": ""' in (tmp_path / "f.html").read_text(encoding="utf-8")


def _run(tmp_path, fail_first):
    sync_api = pytest.importorskip("playwright.sync_api")
    out = tmp_path / "f.html"
    collect.make_form(SENTENCES, ["s00001", "s00002", "s00003"], out, endpoint=ENDPOINT)
    bodies, calls = [], {"n": 0}
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()

        def handle(route):
            calls["n"] += 1
            if fail_first and calls["n"] == 1:
                route.abort()
            else:
                bodies.append(route.request.post_data)
                route.fulfill(status=200, body="ok")

        page.route(ENDPOINT, handle)
        page.goto(out.as_uri())
        assert page.locator("#sendnote").is_visible()
        page.check("#consent")
        page.click("#start")
        for i in range(3):
            if i == 1:
                page.click("#skip")
            else:
                page.fill("#query", f"jawab {i} =1+1")
                page.click("#next")
        if fail_first:
            page.wait_for_selector("#retry:visible")
            assert "did not work" in page.inner_text("#sendstatus")
            page.click("#retry")
        page.wait_for_function("document.querySelector('#sendstatus').textContent.includes('were sent')")
        browser.close()
    return bodies


@pytest.mark.parametrize("fail_first", [False, True])
def test_finishing_sends_rows_that_load_back(tmp_path, fail_first):
    bodies = _run(tmp_path, fail_first)
    assert len(bodies) == 1
    rows = json.loads(bodies[0])["rows"]
    assert len(rows) == 3 and len({r["writer"] for r in rows}) == 1
    sheet = tmp_path / "sheet.csv"
    with sheet.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=collect.RESPONSE_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    got, stats = collect.load_responses([str(sheet)])
    assert sorted(r["query"] for r in got) == ["jawab 0 =1+1", "jawab 2 =1+1"]
    assert stats["dropped: skipped or empty"] == 1


def test_two_sets_on_one_website_do_not_share_saved_state(tmp_path):
    """Sets are pages of one site, so a person who did set A must get a fresh set B."""
    import http.server
    import threading

    sync_api = pytest.importorskip("playwright.sync_api")
    collect.make_form(SENTENCES, ["s00001", "s00002"], tmp_path / "a.html", endpoint=ENDPOINT)
    collect.make_form(SENTENCES, ["s00003", "s00004"], tmp_path / "b.html", endpoint=ENDPOINT)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(tmp_path), **k)

        def log_message(self, *a):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    bodies = []
    try:
        with sync_api.sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.route(ENDPOINT, lambda route: (bodies.append(route.request.post_data), route.fulfill(status=200, body="ok")))
            for name in ("a", "b"):
                page.goto(f"{base}/{name}.html")
                assert page.locator("#resume").is_hidden(), f"set {name} resumed another set's answers"
                page.check("#consent")
                page.click("#start")
                for i in range(2):
                    page.fill("#query", f"jawab {name}{i}")
                    page.click("#next")
                page.wait_for_function("document.querySelector('#sendstatus').textContent.includes('were sent')")
                assert page.locator("#send").inner_text() == ""
            browser.close()
    finally:
        server.shutdown()
    assert len(bodies) == 2
    sent = [json.loads(b)["rows"] for b in bodies]
    assert {r["prompt"] for r in sent[0]} == {"s00001", "s00002"}
    assert {r["prompt"] for r in sent[1]} == {"s00003", "s00004"}
    assert sent[0][0]["writer"] != sent[1][0]["writer"]
