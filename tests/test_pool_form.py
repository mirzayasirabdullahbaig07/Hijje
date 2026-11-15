"""The one-form-for-everybody page: random draw, profile, e-mail kept apart, resume, second round."""
import csv
import http.server
import json
import threading

import pytest

from hijje import collect

ENDPOINT = "https://script.example.test/exec"
sync_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture()
def site(tmp_path):
    """30 sentences: ids s00001-s00030; sets a (10, core), b (10), c (10)."""
    tsv = tmp_path / "sent.tsv"
    tsv.write_text("".join(f"جملہ نمبر {i}\tjumla {i}\n" for i in range(1, 31)), encoding="utf-8")
    batches = {"a": [f"s{i:05d}" for i in range(1, 11)],
               "b": [f"s{i:05d}" for i in range(11, 21)],
               "c": [f"s{i:05d}" for i in range(21, 31)]}
    root = tmp_path / "web"
    root.mkdir()
    collect.make_pool_form(str(tsv), batches, ["a"], root / "index.html", per_visit=6,
                           core_per_visit=3, endpoint=ENDPOINT, contact="me")

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(root), **k)

        def log_message(self, *a):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/index.html", batches, root
    server.shutdown()


def _visit(page, url, bodies, fill=None, finish=True, email=None):
    page.goto(url)
    page.check("#consent")
    for k, v in (fill or {}).items():
        page.select_option(f"#{k}", v) if k != "city" else page.fill("#city", v)
    if email:
        page.fill("#email", email)
    page.click("#start")
    seen = []
    for i in range(6):
        seen.append(page.inner_text("#sentence"))
        if not finish and i == 2:
            return seen
        page.fill("#query", f"jawab {i}")
        page.click("#next")
    page.wait_for_function("document.querySelector('#sendstatus').textContent.includes('were sent')")
    return seen


def _install(page, bodies):
    page.route(ENDPOINT, lambda route: (bodies.append(route.request.post_data), route.fulfill(status=200, body="ok")))


def test_each_visitor_gets_six_sentences_three_from_the_core_and_they_differ(site):
    url, batches, _ = site
    core = set(batches["a"])
    drawn = []
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        for _ in range(6):
            ctx = browser.new_context()           # a new person: empty browser storage
            page = ctx.new_page()
            bodies = []
            _install(page, bodies)
            _visit(page, url, bodies)
            rows = json.loads(bodies[0])["rows"]
            ids = [r["prompt"] for r in rows]
            assert len(ids) == 6 and len(set(ids)) == 6
            assert sum(1 for i in ids if i in core) == 3
            drawn.append(frozenset(ids))
            ctx.close()
        browser.close()
    assert len(set(drawn)) > 1, "every visitor got the same sentences"


def test_profile_goes_with_the_answers_and_the_email_stays_apart(site):
    url, _, _ = site
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        bodies = []
        _install(page, bodies)
        _visit(page, url, bodies, fill={"age_group": "25-34", "city": "Lahore", "mother_tongue": "Punjabi",
                                         "education": "Bachelor's", "province": "Punjab", "device": "phone"},
               email="a@example.org")
        browser.close()
    body = json.loads(bodies[0])
    assert body["contact"]["email"] == "a@example.org" and body["contact"]["writer"] == body["rows"][0]["writer"]
    for r in body["rows"]:
        assert "a@example.org" not in json.dumps(r) and "email" not in r
        assert (r["age_group"], r["city"], r["mother_tongue"], r["education"]) == ("25-34", "Lahore", "Punjabi", "Bachelor's")


def test_no_email_means_no_contact_record(site):
    url, _, _ = site
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        bodies = []
        _install(page, bodies)
        _visit(page, url, bodies)
        browser.close()
    assert "contact" not in json.loads(bodies[0])


def test_reload_in_the_middle_resumes_the_same_sentences(site):
    url, _, _ = site
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        bodies = []
        _install(page, bodies)
        first = _visit(page, url, bodies, finish=False)
        page.reload()
        assert page.locator("#resume").is_visible()
        page.check("#consent")
        page.click("#start")
        assert page.inner_text("#sentence") == first[2], "resumed at a different sentence"
        browser.close()


def test_second_round_gives_new_sentences_and_the_same_writer(site):
    url, _, _ = site
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        bodies = []
        _install(page, bodies)
        _visit(page, url, bodies)
        page.click("#again")
        page.wait_for_selector("#consent")
        _visit(page, url, bodies)
        browser.close()
    r1, r2 = (json.loads(b)["rows"] for b in bodies)
    assert not {r["prompt"] for r in r1} & {r["prompt"] for r in r2}, "a sentence was asked twice"
    assert r1[0]["writer"] == r2[0]["writer"]


def test_failed_send_is_retried_after_a_reload(site):
    url, _, _ = site
    bodies = []
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.route(ENDPOINT, lambda route: route.abort())
        page.goto(url)
        page.check("#consent")
        page.click("#start")
        for i in range(6):
            page.fill("#query", f"jawab {i}")
            page.click("#next")
        page.wait_for_selector("#retry:visible")
        page.unroute(ENDPOINT)
        _install(page, bodies)
        page.reload()                                 # internet is back; the page sends what it kept
        page.wait_for_function("document.querySelector('#sendstatus').textContent.includes('were sent')")
        browser.close()
    assert len(json.loads(bodies[0])["rows"]) == 6


def test_the_answers_load_back_with_the_profile(site, tmp_path):
    url, _, _ = site
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        bodies = []
        _install(page, bodies)
        _visit(page, url, bodies, fill={"age_group": "18-24"})
        browser.close()
    rows = json.loads(bodies[0])["rows"]
    f = tmp_path / "sheet.csv"
    with f.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=collect.RESPONSE_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    got, stats = collect.load_responses([str(f)])
    assert len(got) == 6 and {r["age_group"] for r in got} == {"18-24"}


def test_settings_are_checked(tmp_path):
    tsv = tmp_path / "s.tsv"
    tsv.write_text("".join(f"ا{i}\tx{i}\n" for i in range(1, 8)), encoding="utf-8")
    b = {"a": ["s00001", "s00002"], "b": ["s00003", "s00004", "s00005"]}
    with pytest.raises(ValueError):
        collect.make_pool_form(str(tsv), b, ["z"], tmp_path / "o.html")
    with pytest.raises(ValueError):
        collect.make_pool_form(str(tsv), b, ["a"], tmp_path / "o.html", per_visit=4, core_per_visit=3)
    with pytest.raises(ValueError):
        collect.make_pool_form(str(tsv), b, ["a"], tmp_path / "o.html", per_visit=5, core_per_visit=1)
    with pytest.raises(ValueError):
        collect.make_pool_form(str(tsv), b, ["a"], tmp_path / "o.html", endpoint="http://x")
    assert collect.make_pool_form(str(tsv), b, ["a"], tmp_path / "o.html", per_visit=3, core_per_visit=1)["core"] == 2


def test_output_folder_is_created(tmp_path):
    tsv = tmp_path / "s.tsv"
    tsv.write_text("".join(f"ا{i}\tx{i}\n" for i in range(1, 8)), encoding="utf-8")
    out = tmp_path / "new" / "folder" / "index.html"
    collect.make_pool_form(str(tsv), {"a": ["s00001", "s00002"], "b": ["s00003", "s00004"]}, ["a"], out, per_visit=2, core_per_visit=1)
    assert out.exists()
