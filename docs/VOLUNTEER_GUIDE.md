# Collecting real queries: the volunteer kit

Everything so far used queries that were invented or constructed. A paper needs
**real people typing real queries in their own spelling**. This kit collects
them with no budget, no server and no account.

## What a volunteer does

They see 40 short Urdu sentences, one at a time, written in **Urdu script**
(so no Roman spelling is suggested to them). For each one they type the search
they would use, in Roman Urdu, as they normally type. About 15 minutes. At the
end they download a small CSV file and send it to you.

- Anonymous: the form asks for no name, e-mail or phone number. A random code
  identifies a writer. Optional: device, province, how often they write Roman Urdu.
- 18 or older, with a consent tick box. The consent text says the answers
  (without personal details) may be published as an open dataset.
- Nothing is uploaded. Answers stay in the volunteer's browser until they
  download the file themselves.

## How many people, and who

Aim for **8 to 10 writers**: 40 prompts × 8 writers = 320 queries, which meets
the roadmap targets for M5 (300+ queries) and M6 (5+ writers per query). More
is better. Mix on purpose, because spelling habits differ: different provinces,
ages, education, and phone against computer. Ten people from one class would
mostly share one habit.

## Receive answers automatically (v0.6.1)

Without this, every volunteer must download a file and send it back. With it, the
form sends the answers to a Google Sheet you own when the person presses the last
button. Free, no server. One-time setup, about 10 minutes.

1. Go to https://sheets.google.com and create a blank sheet named `Hijje answers`.
2. In it: **Extensions → Apps Script**. Delete the sample code, paste the whole
   content of `tools/google_apps_script.js` from this repository, press **Save**.
3. **Deploy → New deployment**. Click the gear next to "Select type" → **Web app**.
   Set *Execute as*: **Me**, *Who has access*: **Anyone**. Press **Deploy** and
   allow the permissions Google asks for (it says "unverified app": choose
   Advanced → Go to project; this is your own script).
4. Copy the **Web app URL** (starts with `https://script.google.com/macros/s/...`).
5. Make the forms with that address:

```powershell
python -m hijje make-kit --src $UR --out kit --contact "your contact" --endpoint "PASTE-THE-URL-HERE"
```

Test it yourself first: open `kit/forms/a.html`, answer three sentences, press
through to the end. A sheet tab called `answers` appears with your rows.
(If you edit the script later, use Deploy → Manage deployments → edit → new
version; the address stays the same.)

**Getting the data out:** in the sheet, **File → Download → Comma-separated
values (.csv)**, save it into your `answers/` folder, and run `collect-build` as
before. The sheet has the same columns as the form's CSV (plus `received_at`,
which is ignored), and if a person sends twice only the last answer per
sentence is kept.

**Things to know**
- The form tells volunteers their answers are sent when they finish, and nothing
  before. It still offers the CSV download if sending fails (for example no
  internet), so no one's work is lost.
- Anyone who has the web app address can post rows to it. The script limits each
  post to 200 rows and 300 characters per cell and stores everything as plain
  text, so nothing can run as a formula. Do not publish the address widely; give
  it only inside the forms. Bad rows are easy to delete from the sheet.
- The browser cannot read Google's reply, so "sent" means the request left the
  phone. Check the sheet after the first few volunteers.
- Google Sheets stores the data in your Google account. The form already says
  answers are anonymous; do not add a name column.

## The large pool: 14 sets, 549 sentences (v0.6)

`data/real_queries/` holds 14 sets of prompt sentence numbers (`prompt_ids.txt` is
set A, then `prompt_ids_b.txt` ... `prompt_ids_n.txt`). 549 distinct sentences, 40
each (set N has 29), screened to be self-contained and safe to ask a stranger
about. Only numbers are committed, never the CC BY-SA sentences.

**How to use them.** The research question about spelling needs *several people
writing the same prompt*. So:

- **Sets A, B, C (120 prompts): give each to at least 5 different people.** This
  is what the "5+ writers per query" milestone (M6) measures.
- **Sets D to N (429 prompts): 1 or 2 people per set is fine.** They add many
  more distinct queries (M5: 300+), but with one writer you cannot compare
  spellings of the same prompt.
- One person should answer **one set only**. 40 sentences is already about
  15 minutes; more gives tired, careless answers.

No tool can make the answers: they must come from real people. A realistic
target is 10 to 15 people. That gives 400 to 600 real queries.

**Make everything in one command** (forms, Excel sheets, WhatsApp texts):

```powershell
python -m hijje make-kit --src $UR --out kit --contact "your contact" --intro "Please type, for each sentence, the words you would type to search for it, in Roman Urdu. 1) question number then your words."
```

This creates three folders, each with one file per set (`a`, `b`, ... `n`):

| Folder | For people who... | What they send back |
| --- | --- | --- |
| `kit/forms/x.html` | can open a web page (host it as above, one page per set) | the CSV the form downloads |
| `kit/sheets/x.csv` | prefer Excel or Google Sheets | the same file with column D (`query`) filled; save as **CSV UTF-8** |
| `kit/whatsapp/x.txt` | only use WhatsApp or SMS | a reply typed as `1) words`, `2) words` ... |

In a sheet, column A already has a writer code (`WA` for set A). **Change it to a
different code for every person** before sending (`P01`, `P02` ...), otherwise
two people look like one. Keep a private list of which code went to whom.

**Turn a WhatsApp reply into an answer file.** Save the person's message as a
text file (copy and paste into Notepad, save as UTF-8), then:

```powershell
python -m hijje import-text --reply reply_P03.txt --prompts data/real_queries/prompt_ids_b.txt --writer P03 --out answers/P03.csv
```

It prints how many answers it found and how many lines it could not use (no
number, number not in the list, number repeated). Nothing is guessed. All the
files from all formats go into the same `answers/` folder and `collect-build`
reads them together.

## Step by step

All commands run in the VS Code terminal in your `hijje` folder. `$UR` is the
Dakshina Urdu folder: `$UR = "C:\Users\HP\Downloads\dakshina\dakshina_dataset_v1.0\ur"`.

**1. Make the form** (a single file, `form.html`; it is ignored by git because it
contains CC BY-SA sentences):

```powershell
python -m hijje make-form --src $UR --out form.html --contact "your WhatsApp number or e-mail"
```

Open `form.html` in your own browser first and answer two or three prompts to
see what a volunteer sees.

**2. Give people a link.** A file sent over WhatsApp is hard to open on a phone,
so host it for free:

1. On GitHub create a new **public** repository, for example `hijje-form`.
2. Upload `form.html` and rename it to `index.html`.
3. Settings → Pages → Branch `main`, folder `/ (root)` → Save.
4. After a minute the page is at `https://<your-username>.github.io/hijje-form/`.

The form shows its own CC BY-SA attribution line, as the licence of the
sentences requires. Never put your own contact details in a repository if you
do not want them public: the `--contact` text is visible to anyone with the link.

**3. Invite people.** A message you can paste (the Urdu is in Urdu script on
purpose, so it does not suggest a spelling):

> السلام علیکم! میں رومن اردو میں سرچ پر ایک چھوٹی سی تحقیق کر رہا/رہی ہوں۔ اس لنک پر 40 مختصر اردو جملے ہیں۔ ہر جملے کے لیے بس وہ لکھ دیں جو آپ اسے ڈھونڈنے کے لیے رومن اردو میں لکھیں گے۔ تقریباً 15 منٹ لگیں گے، نام یا نمبر نہیں مانگا جاتا، اور کوئی جواب غلط نہیں۔ آخر میں فائل ڈاؤن لوڈ کر کے مجھے بھیج دیں۔ شکریہ!
>
> (link)

Tell them: do not look words up, do not ask anyone how to spell, and do not
copy from the sentence. Type quickly, the way they would on their phone.

**4. Collect the files.** Save every returned `hijje_answers_*.csv` into
`data\real_queries\answers\`. These files are anonymous and the volunteers
consented to publication, so they can be committed.

**5. Build and check:**

```powershell
python -m hijje collect-build --responses "data\real_queries\answers\*.csv" --src $UR --out data\real_built
```

It prints how many rows were kept and why others were dropped (skipped,
typed in Urdu script, too long), how many writers each prompt has, and how
much two writers' queries for the same prompt overlap in words. Look at the
dropped counts: many "typed in Urdu script" rows mean the instructions were
not clear to someone.

**6. Judge the pooled results.** A query can also be answered by sentences
other than the one it was written from. The standard fix is pooling: collect
the top results of several retrievers and have a person grade them.

```powershell
python -m hijje judge-sheet --data data\real_built --src $UR --out judge.csv
```

Open `judge.csv` in Excel. In the `grade` column write 2 if the passage gives
the information the prompt sentence gives, 1 if partly, 0 if not (blank = not
judged). Each row is one prompt and one passage and applies to every writer of
that prompt. Expect roughly 400 to 600 rows: about an hour. **Ask a second
person to grade the same sheet** and compare; that agreement belongs in the
paper. Then keep only the grades (no sentence text, safe to commit):

```powershell
python -m hijje judge-export --sheet judge.csv --out data\real_queries\judgments.csv
```

**7. Rebuild with the grades and evaluate:**

```powershell
python -m hijje collect-build --responses "data\real_queries\answers\*.csv" --src $UR --out data\real_built --judgments data\real_queries\judgments.csv
python -m hijje real-eval --data data\real_built --out results\real
```

`results\real\summary.md` is the first result on real queries. It reports nDCG,
recall and MRR averaged per prompt, the **worst writer** per prompt (the one
with the unlucky spelling), and **agreement** (do two writers' queries return
the same top results?).

## What the result can and cannot say

It can say how much real spelling variation hurts search on real
queries, and whether level 3 or 4 recovers it. It cannot say how people type in
chat, because the passages are encyclopaedia sentences and the volunteers know
they are in a study. State both limits. The queries are also tied to
40 prompts, so report the number of prompts, not only the number of queries:
the statistics in `real-eval` are averaged per prompt for that reason.

## If something goes wrong

- **The download button does nothing** (some in-app browsers): the page has a
  "The download does not work" box with the answers as text. Ask the volunteer
  to copy it into a message; save it as a `.csv` file yourself.
- **A volunteer typed Urdu script**: those rows are dropped and counted. Ask
  them to redo it in Roman letters.
- **Someone's answers are all one word or look careless**: keep the file but
  check the writer's queries; remove the file if they clearly were not trying.
  Write down why.
- **A volunteer wants their answers removed**: delete their file. Their code
  is in the file name.
