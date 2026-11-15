"""One form for everybody: every visitor gets a different small random set of sentences.

``collect.make_pool_form`` replaces __PAYLOAD__. All sentences of the pool are
inside the page. When a person presses Start, the page draws a few sentences at
random: some from the "core" sets (so that these get many writers) and the rest
from all other sentences. Answers are sent to the endpoint when the person
finishes. A CSV download stays as a fallback.
"""

from .form_template import FORM_HTML

_STYLE = FORM_HTML[FORM_HTML.index("<style>"): FORM_HTML.index("</style>") + len("</style>")].replace(
    "select, textarea {", "select, textarea, input[type=text], input[type=email] {"
)

POOL_FORM_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
__STYLE__
</head>
<body>
<main>
  <h1 id="title"></h1>
  <p class="muted" id="subtitle"></p>

  <section id="intro" class="card">
    <p class="ur">آپ کو اردو کے چند جملے دکھائے جائیں گے۔ ہر جملے کے لیے سوچیں کہ اسے انٹرنیٹ یا چیٹ میں ڈھونڈنے کے لیے آپ کیا لکھیں گے، اور وہی <b>رومن اردو</b> میں اسی طرح لکھیں جیسے آپ عام طور پر لکھتے ہیں۔ کوئی جواب غلط نہیں ہے۔ اسپیلنگ کی فکر نہ کریں: ہمیں آپ کی اپنی لکھائی چاہیے۔</p>
    <p>You will see a few Urdu sentences, one at a time (about <span id="count"></span>, roughly <span id="minutes"></span> minutes). For each, imagine you want to find that sentence by searching the internet or asking in a chat. <b>Type that search, in Roman Urdu, the way you normally type.</b> There are no wrong answers. Do not worry about spelling: your own way of writing is exactly what we want to study.</p>
    <div class="note">
      <b>Please:</b> type quickly and naturally, as you would on your phone. Do not look anything up and do not ask anyone how a word is spelled.
    </div>
    <h2 style="font-size:1.05rem">Before you start</h2>
    <p class="muted">Your answers are anonymous: they are stored under a random code, not your name. The questions below are optional. Your answers and your age group, province, mother tongue and education may be published as an open research dataset. <b>Your city and e-mail are never published.</b> If you leave an e-mail, it is stored in a separate list and used only to thank you and to tell you the results. You can stop at any time by closing this page.</p>
    <p class="muted hidden" id="sendnote">When you finish, your answers are sent automatically to the researcher. Nothing is sent before that.</p>
    <label style="font-weight:400"><input type="checkbox" id="consent"> I am 18 or older, and I agree that my answers may be used and published this way.</label>

    <label for="age_group">Age group (optional)</label>
    <select id="age_group"><option value="">–</option><option>18-24</option><option>25-34</option><option>35-44</option><option>45-54</option><option>55+</option></select>
    <label for="city">City (optional)</label>
    <input type="text" id="city" maxlength="40" autocomplete="off">
    <label for="province">Province or region (optional)</label>
    <select id="province"><option value="">–</option><option>Punjab</option><option>Sindh</option><option>Khyber Pakhtunkhwa</option><option>Balochistan</option><option>Islamabad</option><option>Azad Kashmir</option><option>Gilgit-Baltistan</option><option>Outside Pakistan</option></select>
    <label for="mother_tongue">Mother tongue (optional)</label>
    <select id="mother_tongue"><option value="">–</option><option>Urdu</option><option>Punjabi</option><option>Saraiki</option><option>Sindhi</option><option>Pashto</option><option>Balochi</option><option>Other</option></select>
    <label for="education">Education (optional)</label>
    <select id="education"><option value="">–</option><option>Matric or below</option><option>Intermediate</option><option>Bachelor's</option><option>Master's or above</option></select>
    <label for="device">What are you typing on? (optional)</label>
    <select id="device"><option value="">–</option><option>phone</option><option>tablet</option><option>computer</option></select>
    <label for="frequency">How often do you write Roman Urdu? (optional)</label>
    <select id="frequency"><option value="">–</option><option>daily</option><option>weekly</option><option>rarely</option></select>
    <label for="email">E-mail, if you would like to hear the results (optional)</label>
    <input type="email" id="email" maxlength="80" autocomplete="off">

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
    <p>You answered <b id="answered"></b> of <b id="total"></b> sentences.</p>
    <p id="sendstatus" class="hidden"></p>
    <div class="row hidden" id="retryrow"><button class="primary" id="retry">Send again</button></div>
    <div class="row hidden" id="againrow"><button class="primary" id="again">Answer a few more sentences</button></div>
    <div id="fallback" class="hidden">
      <p>Please download your answers and send the file back.</p>
      <div class="row"><button class="primary" id="download">Download my answers</button></div>
      <p class="muted" id="send"></p>
      <details><summary>The download does not work</summary>
        <p class="muted">Copy everything in the box below into a message or a note and send it instead.</p>
        <textarea class="csv" id="csvbox" readonly></textarea>
      </details>
    </div>
  </section>
  <p class="muted" style="font-size:.8rem">The Urdu sentences are taken from the Dakshina dataset (Google Research, Roark et al. 2020), licence CC BY-SA 4.0.</p>
</main>

<script id="config" type="application/json">__PAYLOAD__</script>
<script>
(function () {
  "use strict";
  var CONFIG = JSON.parse(document.getElementById("config").textContent);
  var POOL = CONFIG.prompts, PER = CONFIG.per_visit, CORE_N = CONFIG.core_per_visit;
  var COLUMNS = ["writer", "prompt", "status", "query", "device", "province", "frequency", "age_group", "city", "mother_tongue", "education"];
  var META = ["device", "province", "frequency", "age_group", "city", "mother_tongue", "education"];
  var K_WRITER = "hijje-pool-writer-v1", K_DONE = "hijje-pool-done-v1", K_SESSION = "hijje-pool-session-v1";
  var $ = function (id) { return document.getElementById(id); };
  var byId = {}; POOL.forEach(function (p) { byId[p.id] = p; });
  var state = null;

  function get(k) { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch (e) { return null; } }
  function put(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode: keep going in memory */ } }
  function drop(k) { try { localStorage.removeItem(k); } catch (e) { } }

  $("title").textContent = CONFIG.title;
  $("subtitle").textContent = "A few short sentences, about " + Math.max(3, Math.round(PER * 0.4)) + " minutes";
  $("count").textContent = PER + " sentences"; $("minutes").textContent = Math.max(3, Math.round(PER * 0.4));

  function randInt(n) { var b = new Uint32Array(1); (window.crypto || window.msCrypto).getRandomValues(b); return b[0] % n; }
  function sample(arr, k) {                         // k distinct items, in random order
    var a = arr.slice(), out = [];
    while (out.length < k && a.length) { out.push(a.splice(randInt(a.length), 1)[0]); }
    return out;
  }
  function newCode() {
    var letters = "abcdefghjkmnpqrstuvwxyz23456789", out = "w-";
    var buf = new Uint32Array(6); (window.crypto || window.msCrypto).getRandomValues(buf);
    for (var i = 0; i < 6; i++) out += letters[buf[i] % letters.length];
    return out;
  }
  function draw() {
    var done = get(K_DONE) || [], seen = {}; done.forEach(function (id) { seen[id] = 1; });
    var fresh = POOL.filter(function (p) { return !seen[p.id]; });
    if (fresh.length < PER) { fresh = POOL.slice(); }       // this person has answered nearly everything
    var core = fresh.filter(function (p) { return p.core; }), rest = fresh.filter(function (p) { return !p.core; });
    var a = sample(core, Math.min(CORE_N, core.length));
    var b = sample(rest, Math.min(PER - a.length, rest.length));
    var chosen = a.concat(b);
    if (chosen.length < PER) {
      var taken = {}; chosen.forEach(function (p) { taken[p.id] = 1; });
      chosen = chosen.concat(sample(fresh.filter(function (p) { return !taken[p.id]; }), PER - chosen.length));
    }
    return sample(chosen, chosen.length).map(function (p) { return p.id; });   // shuffled
  }

  function show(id) { ["intro", "ask", "done"].forEach(function (s) { $(s).classList.toggle("hidden", s !== id); }); window.scrollTo(0, 0); }
  function n() { return state.ids.length; }

  function render() {
    var p = byId[state.ids[state.pos]];
    $("sentence").textContent = p.text;
    $("counter").textContent = "Sentence " + (state.pos + 1) + " of " + n();
    $("progress").style.width = (100 * state.pos / n()) + "%";
    var prev = state.answers[p.id];
    $("query").value = prev && prev.status === "ok" ? prev.query : "";
    $("back").disabled = state.pos === 0;
    $("next").textContent = state.pos === n() - 1 ? "Finish" : "Next";
    $("next").disabled = $("query").value.trim() === "";
    show("ask");
    $("query").focus();
  }
  function record(status) {
    var id = state.ids[state.pos];
    state.answers[id] = { status: status, query: status === "ok" ? $("query").value.replace(/\s+/g, " ").trim() : "" };
    put(K_SESSION, state);
  }
  function advance() { if (state.pos < n() - 1) { state.pos++; put(K_SESSION, state); render(); } else { finish(); } }

  function rows() {
    var out = [];
    state.ids.forEach(function (id) {
      var a = state.answers[id]; if (!a) return;
      var r = { writer: state.writer, prompt: id, status: a.status, query: a.query };
      META.forEach(function (k) { r[k] = state.meta[k] || ""; });
      out.push(r);
    });
    return out;
  }
  function csvCell(v) { v = String(v == null ? "" : v); return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }
  function buildCsv() {
    var lines = [COLUMNS.join(",")];
    rows().forEach(function (r) { lines.push(COLUMNS.map(function (c) { return csvCell(r[c]); }).join(",")); });
    return lines.join("\r\n") + "\r\n";
  }
  function markDone() {
    var done = get(K_DONE) || [];
    state.ids.forEach(function (id) { if (done.indexOf(id) < 0) done.push(id); });
    put(K_DONE, done);
  }
  function sendAnswers() {
    var st = $("sendstatus"); st.classList.remove("hidden"); $("retryrow").classList.add("hidden");
    st.textContent = "Sending your answers...";
    var body = { rows: rows() };
    if (state.email) { body.contact = { writer: state.writer, email: state.email }; }
    fetch(CONFIG.endpoint, { method: "POST", mode: "no-cors", headers: { "Content-Type": "text/plain;charset=utf-8" }, body: JSON.stringify(body) })
      .then(function () {
        state.sent = true; put(K_SESSION, state);
        st.textContent = "Your answers were sent. Thank you!";
        $("fallback").classList.add("hidden"); $("againrow").classList.remove("hidden");
      })
      .catch(function () {
        st.textContent = "Sending did not work (no internet?). Press Send again, or download the file below and send it to us.";
        $("fallback").classList.remove("hidden");
        if (CONFIG.contact) { $("send").textContent = "Send the file to: " + CONFIG.contact; }
        $("retryrow").classList.remove("hidden");
      });
  }
  function finish() {
    state.finished = true; markDone(); put(K_SESSION, state);
    var answered = state.ids.filter(function (id) { return state.answers[id] && state.answers[id].status === "ok"; }).length;
    $("answered").textContent = answered; $("total").textContent = n();
    $("csvbox").value = buildCsv();
    $("progress").style.width = "100%";
    show("done");
    if (CONFIG.endpoint) { sendAnswers(); }
    else { $("fallback").classList.remove("hidden"); $("send").textContent = CONFIG.contact ? "Send the file to: " + CONFIG.contact : ""; }
  }
  if (CONFIG.endpoint) { $("sendnote").classList.remove("hidden"); $("retry").addEventListener("click", sendAnswers); }

  $("consent").addEventListener("change", function () { $("start").disabled = !$("consent").checked; });
  $("again").addEventListener("click", function () { drop(K_SESSION); location.reload(); });
  $("start").addEventListener("click", function () {
    var saved = get(K_SESSION);
    if (saved && saved.ids && !saved.finished) { state = saved; }
    else {
      var writer = get(K_WRITER); if (!writer) { writer = newCode(); put(K_WRITER, writer); }
      state = { writer: writer, ids: draw(), pos: 0, answers: {}, meta: {}, email: "", sent: false, finished: false };
      META.forEach(function (k) { state.meta[k] = $(k).value.trim(); });
      state.email = $("email").value.trim();
    }
    put(K_SESSION, state); render();
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

  var saved = get(K_SESSION);
  if (saved && saved.ids && saved.ids.every(function (id) { return byId[id]; })) {
    if (saved.finished && !saved.sent) { state = saved; finish(); }          // answers not sent yet: try again
    else if (!saved.finished && Object.keys(saved.answers).length) {
      $("resume").classList.remove("hidden");
      $("resume").textContent = "You already answered " + Object.keys(saved.answers).length + " sentences on this device. Press Start to carry on where you stopped.";
    }
  }
})();
</script>
</body>
</html>
""".replace("__STYLE__", _STYLE)
