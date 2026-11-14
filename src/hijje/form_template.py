"""The volunteer form: one self-contained HTML file, no server, no account.

``collect.make_form`` replaces __PAYLOAD__ (the prompts, as JSON) and __TITLE__.
The page keeps answers in the browser and gives the volunteer a CSV file to send
back. Nothing is uploaded anywhere.
"""

FORM_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { --bg:#f7f6f2; --card:#ffffff; --ink:#1f2328; --muted:#5b636b; --line:#d9d6cc; --accent:#1b6b57; --accent-ink:#ffffff; --warn:#8a4b00; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#16191c; --card:#1f2327; --ink:#e8e6e1; --muted:#a2a9b0; --line:#38403f; --accent:#4fb79a; --accent-ink:#0b1512; --warn:#e0a458; }
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
  main { max-width:640px; margin:0 auto; padding:20px 16px 56px; }
  h1 { font-size:1.35rem; margin:8px 0 4px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px; margin:14px 0; }
  .ur { direction:rtl; text-align:right; font-family:"Noto Nastaliq Urdu","Jameel Noori Nastaleeq","Urdu Typesetting","Segoe UI",Tahoma,serif; line-height:2.1; }
  .sentence { font-size:1.45rem; }
  .muted { color:var(--muted); font-size:.92rem; }
  label { display:block; margin:12px 0 4px; font-weight:600; }
  select, textarea { width:100%; padding:10px; font:inherit; color:var(--ink); background:var(--bg); border:1px solid var(--line); border-radius:8px; }
  textarea { min-height:84px; resize:vertical; }
  button { font:inherit; padding:11px 18px; border-radius:8px; border:1px solid var(--line); background:var(--card); color:var(--ink); cursor:pointer; }
  button.primary { background:var(--accent); color:var(--accent-ink); border-color:var(--accent); font-weight:600; }
  button:disabled { opacity:.45; cursor:not-allowed; }
  .row { display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; align-items:center; }
  .bar { height:8px; background:var(--line); border-radius:6px; overflow:hidden; }
  .bar > div { height:100%; background:var(--accent); width:0; transition:width .2s; }
  .hidden { display:none; }
  .note { border-left:4px solid var(--warn); padding:6px 12px; margin:12px 0; }
  code { background:var(--bg); padding:1px 6px; border-radius:5px; }
  textarea.csv { font-family:ui-monospace,Consolas,monospace; font-size:.8rem; min-height:140px; direction:ltr; }
  :focus-visible { outline:3px solid var(--accent); outline-offset:2px; }
</style>
</head>
<body>
<main>
  <h1 id="title"></h1>
  <p class="muted" id="subtitle"></p>

  <section id="intro" class="card">
    <p class="ur">آپ کو اردو کے کچھ جملے دکھائے جائیں گے۔ ہر جملے کے لیے سوچیں کہ اسے انٹرنیٹ یا چیٹ میں ڈھونڈنے کے لیے آپ کیا لکھیں گے، اور وہی <b>رومن اردو</b> میں اسی طرح لکھیں جیسے آپ عام طور پر لکھتے ہیں۔ کوئی جواب غلط نہیں ہے۔ اسپیلنگ کی فکر نہ کریں: ہمیں آپ کی اپنی لکھائی چاہیے۔</p>
    <p>You will see Urdu sentences, one at a time. For each, imagine you want to find that sentence by searching the internet or asking in a chat. <b>Type that search, in Roman Urdu, the way you normally type.</b> There are no wrong answers. Do not worry about spelling: your own way of writing is exactly what we want to study.</p>
    <p class="muted" id="duration"></p>
    <div class="note">
      <b>Please:</b> type quickly and naturally, as you would on your phone. Do not look anything up and do not ask anyone how a word is spelled. If your keyboard changes words by itself, that is fine.
    </div>
    <h2 style="font-size:1.05rem">Before you start</h2>
    <p class="muted">This is anonymous. We do not ask for your name, e-mail or phone number. Your answers will be used for research on Roman Urdu search and may be published, without any personal details, as an open dataset. You can stop at any time by closing this page.</p>
    <label style="font-weight:400"><input type="checkbox" id="consent"> I am 18 or older, and I agree that my answers may be used and published this way.</label>
    <label for="device">What are you typing on? (optional)</label>
    <select id="device"><option value="">–</option><option>phone</option><option>tablet</option><option>computer</option></select>
    <label for="province">Where do you live? (optional)</label>
    <select id="province"><option value="">–</option><option>Punjab</option><option>Sindh</option><option>Khyber Pakhtunkhwa</option><option>Balochistan</option><option>Islamabad</option><option>Azad Kashmir</option><option>Gilgit-Baltistan</option><option>Outside Pakistan</option></select>
    <label for="frequency">How often do you write Roman Urdu? (optional)</label>
    <select id="frequency"><option value="">–</option><option>daily</option><option>weekly</option><option>rarely</option></select>
    <div class="row"><button class="primary" id="start" disabled>Start</button></div>
    <p class="muted hidden" id="resume"></p>
  </section>

  <section id="ask" class="card hidden">
    <div class="bar" aria-hidden="true"><div id="progress"></div></div>
    <p class="muted" id="counter" aria-live="polite"></p>
    <p class="ur sentence" id="sentence" lang="ur"></p>
    <label for="query">Your search, in Roman Urdu</label>
    <textarea id="query" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false" lang="ur-Latn" placeholder="e.g. a short search or question"></textarea>
    <div class="row">
      <button id="back">Back</button>
      <button class="primary" id="next" disabled>Next</button>
      <button id="skip">I do not understand this sentence</button>
    </div>
  </section>

  <section id="done" class="card hidden">
    <h2 style="margin-top:0">Thank you!</h2>
    <p>You answered <b id="answered"></b> of <b id="total"></b> sentences. Please download your answers and send the file back.</p>
    <div class="row"><button class="primary" id="download">Download my answers</button></div>
    <p class="muted" id="send"></p>
    <details><summary>The download does not work</summary>
      <p class="muted">Copy everything in the box below into a message or a note and send it instead.</p>
      <textarea class="csv" id="csvbox" readonly></textarea>
    </details>
  </section>
  <p class="muted" style="font-size:.8rem">The Urdu sentences are taken from the Dakshina dataset (Google Research, Roark et al. 2020), licence CC BY-SA 4.0.</p>
</main>

<script id="config" type="application/json">__PAYLOAD__</script>
<script>
(function () {
  "use strict";
  var CONFIG = JSON.parse(document.getElementById("config").textContent);
  var PROMPTS = CONFIG.prompts;
  var COLUMNS = ["writer", "prompt", "status", "query", "device", "province", "frequency"];
  var STORE_KEY = "hijje-form-v1";
  var $ = function (id) { return document.getElementById(id); };

  document.getElementById("title").textContent = CONFIG.title;
  $("subtitle").textContent = PROMPTS.length + " short sentences";
  $("duration").textContent = "It takes about " + Math.max(5, Math.round(PROMPTS.length * 0.35)) + " minutes.";

  var state = { writer: "", order: [], pos: 0, answers: {}, meta: { device: "", province: "", frequency: "" } };

  function load() { try { return JSON.parse(localStorage.getItem(STORE_KEY) || "null"); } catch (e) { return null; } }
  function save() { try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* private mode: keep going in memory */ } }

  function newCode() {
    var letters = "abcdefghjkmnpqrstuvwxyz23456789", out = "w-";
    var buf = new Uint32Array(6);
    (window.crypto || window.msCrypto).getRandomValues(buf);
    for (var i = 0; i < 6; i++) out += letters[buf[i] % letters.length];
    return out;
  }
  function seededOrder(code, n) {          // a different order for each writer, fixed for one writer
    var h = 2166136261;
    for (var i = 0; i < code.length; i++) { h ^= code.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    function rnd() { h += 0x6D2B79F5; var t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
    var a = []; for (var k = 0; k < n; k++) a.push(k);
    for (var j = n - 1; j > 0; j--) { var r = Math.floor(rnd() * (j + 1)); var tmp = a[j]; a[j] = a[r]; a[r] = tmp; }
    return a;
  }
  function show(id) { ["intro", "ask", "done"].forEach(function (s) { $(s).classList.toggle("hidden", s !== id); }); window.scrollTo(0, 0); }

  function render() {
    var idx = state.order[state.pos], p = PROMPTS[idx];
    $("sentence").textContent = p.text;
    $("counter").textContent = "Sentence " + (state.pos + 1) + " of " + PROMPTS.length;
    $("progress").style.width = (100 * state.pos / PROMPTS.length) + "%";
    var prev = state.answers[p.id];
    $("query").value = prev && prev.status === "ok" ? prev.query : "";
    $("back").disabled = state.pos === 0;
    $("next").textContent = state.pos === PROMPTS.length - 1 ? "Finish" : "Next";
    $("next").disabled = $("query").value.trim() === "";
    show("ask");
    $("query").focus();
  }
  function record(status) {
    var p = PROMPTS[state.order[state.pos]];
    state.answers[p.id] = { status: status, query: status === "ok" ? $("query").value.replace(/\s+/g, " ").trim() : "" };
    save();
  }
  function advance() {
    if (state.pos < PROMPTS.length - 1) { state.pos++; save(); render(); } else { finish(); }
  }
  function csvCell(v) { v = String(v == null ? "" : v); return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }
  function buildCsv() {
    var lines = [COLUMNS.join(",")];
    PROMPTS.forEach(function (p) {
      var a = state.answers[p.id]; if (!a) return;
      lines.push([state.writer, p.id, a.status, a.query, state.meta.device, state.meta.province, state.meta.frequency].map(csvCell).join(","));
    });
    return lines.join("\r\n") + "\r\n";
  }
  function finish() {
    var answered = Object.keys(state.answers).filter(function (k) { return state.answers[k].status === "ok"; }).length;
    $("answered").textContent = answered; $("total").textContent = PROMPTS.length;
    $("csvbox").value = buildCsv();
    $("send").textContent = CONFIG.contact ? "Send the file to: " + CONFIG.contact : "Send the downloaded file to the person who gave you this page.";
    $("progress").style.width = "100%";
    save(); show("done");
  }

  $("consent").addEventListener("change", function () { $("start").disabled = !$("consent").checked; });
  $("start").addEventListener("click", function () {
    var saved = load();
    if (saved && saved.writer && saved.order && saved.order.length === PROMPTS.length) { state = saved; }
    else {
      state.writer = newCode(); state.order = seededOrder(state.writer, PROMPTS.length); state.pos = 0; state.answers = {}; state.meta = { device: "", province: "", frequency: "" };
    }
    ["device", "province", "frequency"].forEach(function (k) { if ($(k).value) state.meta[k] = $(k).value; });
    save(); render();
  });
  $("query").addEventListener("input", function () { $("next").disabled = $("query").value.trim() === ""; });
  $("next").addEventListener("click", function () { record("ok"); advance(); });
  $("skip").addEventListener("click", function () { record("skip"); advance(); });
  $("back").addEventListener("click", function () { if (state.pos > 0) { state.pos--; render(); } });
  $("download").addEventListener("click", function () {
    var blob = new Blob(["﻿" + buildCsv()], { type: "text/csv;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "hijje_answers_" + state.writer + ".csv";
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  });

  var saved = load();
  if (saved && saved.writer && saved.order && saved.order.length === PROMPTS.length && Object.keys(saved.answers).length) {
    $("resume").classList.remove("hidden");
    $("resume").textContent = "You already answered " + Object.keys(saved.answers).length + " sentences on this device. Press Start to carry on where you stopped.";
  }
})();
</script>
</body>
</html>
"""
