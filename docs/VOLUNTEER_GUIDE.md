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
