// Receives answers from the Hijje form and appends them to a Google Sheet.
// Setup: see docs/VOLUNTEER_GUIDE.md ("Receive answers automatically").
var COLUMNS = ["writer", "prompt", "status", "query", "device", "province", "frequency"];
var MAX_ROWS = 200;      // one person answers at most one set (40 prompts)
var MAX_CELL = 300;      // characters

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var data = JSON.parse(e.postData.contents);
    var rows = (data.rows || []).slice(0, MAX_ROWS);
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("answers") ||
                SpreadsheetApp.getActiveSpreadsheet().insertSheet("answers");
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(COLUMNS.concat(["received_at"]));
    }
    var now = new Date().toISOString();
    var values = rows.map(function (r) {
      return COLUMNS.map(function (c) { return String(r[c] == null ? "" : r[c]).slice(0, MAX_CELL); }).concat([now]);
    });
    if (values.length) {
      var range = sheet.getRange(sheet.getLastRow() + 1, 1, values.length, COLUMNS.length + 1);
      range.setNumberFormat("@");          // plain text: a query starting with "=" is never run as a formula
      range.setValues(values);
    }
    return ContentService.createTextOutput("ok");
  } finally {
    lock.releaseLock();
  }
}
