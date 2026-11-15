// Receives answers from the Hijje forms and appends them to a Google Sheet.
// Setup: see docs/VOLUNTEER_GUIDE.md ("Receive answers automatically").
//
// Tab "answers":  one row per answer. New columns are added by name, so an
//                 older sheet keeps working when the form gains a question.
// Tab "contacts": e-mail addresses people chose to leave. Never mixed with the
//                 answers and never to be published.
var COLUMNS = ["writer", "prompt", "status", "query", "device", "province", "frequency",
               "age_group", "city", "mother_tongue", "education"];
var MAX_ROWS = 200;      // one visit is at most a few dozen answers
var MAX_CELL = 300;      // characters

function cell_(v) { return String(v == null ? "" : v).slice(0, MAX_CELL); }

function sheet_(name, headers) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(name) || ss.insertSheet(name);
  if (sh.getLastRow() === 0) { sh.appendRow(headers); }
  return sh;
}

// Header row of the sheet, with any missing column added at the end.
function headers_(sh, wanted) {
  var head = sh.getRange(1, 1, 1, Math.max(1, sh.getLastColumn())).getValues()[0].map(String);
  wanted.forEach(function (c) {
    if (head.indexOf(c) < 0) { head.push(c); sh.getRange(1, head.length).setValue(c); }
  });
  return head;
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var data = JSON.parse(e.postData.contents);
    var now = new Date().toISOString();

    var rows = (data.rows || []).slice(0, MAX_ROWS);
    if (rows.length) {
      var sh = sheet_("answers", COLUMNS.concat(["received_at"]));
      var head = headers_(sh, COLUMNS.concat(["received_at"]));
      var values = rows.map(function (r) {
        return head.map(function (c) { return c === "received_at" ? now : cell_(r[c]); });
      });
      var range = sh.getRange(sh.getLastRow() + 1, 1, values.length, head.length);
      range.setNumberFormat("@");          // plain text: a query starting with "=" is never run as a formula
      range.setValues(values);
    }

    var contact = data.contact;
    if (contact && contact.email) {
      var cs = sheet_("contacts", ["writer", "email", "received_at"]);
      var crange = cs.getRange(cs.getLastRow() + 1, 1, 1, 3);
      crange.setNumberFormat("@");
      crange.setValues([[cell_(contact.writer), cell_(contact.email), now]]);
    }
    return ContentService.createTextOutput("ok");
  } finally {
    lock.releaseLock();
  }
}
