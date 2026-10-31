# Element — Edexcel A level Chemistry tracker

A responsive personal tracker for **UK Edexcel A level Chemistry (9CH0)**, populated from the user-supplied **Issue 3, February 2024** specification.

## Run

```sh
cd /workspace/A-level-Chem
python3 server.py
```

`npm start` is equivalent. The server listens on port **3000**. To choose another address, use `python3 server.py --host 127.0.0.1 --port 3001`.

No npm installation or build is required. The application uses Python's standard library and plain browser assets. PDF extraction/rebuilding needs `pdftotext` from Poppler (`poppler-utils` on Debian/Ubuntu), already installed in the cloud environment. The bundled checklist and PDF work without Pearson network access.

## Official checklist

The source is [the uploaded specification](app/specification.pdf), identified by SHA-256:

```text
b01c2b0a26ef82215b56fd45dcd03668efe308890739dd3243ba59982ec36d35
```

The default checklist contains **596 independently tracked entries**:

- **325 numbered subject-content objectives**, across all 19 topics.
- **205 explicit Roman-numbered sub-points**, preserving the parent context. The full parent wording, including qualifications, conditions and examples, is also retained.
- **45 practical requirements**: 10 Appendix 5a abilities, 10 Appendix 5b abilities, 12 Appendix 5c apparatus/technique requirements, 11 Common Practical Assessment Criteria (CPAC), and separate entries for Core Practical 13a and 13b.
- **21 coded Appendix 6 mathematical skills**, with the chemistry exemplifications available in each entry's notes dialog.

All **16 core practical entries** have their official titles and source pages. Practical 13 covers two parts; its parts have separate evidence checkboxes. Practical records support method, results, hazards, uncertainty and evaluation notes.

The generated [coverage audit](app/coverage-audit.json) lists every included reference and the source identity. Appendix 5d (core practical–technique mapping), Appendix 7 (command words), and Appendix 8 (data booklet) are linked as supporting PDF references, rather than counted as additional learning objectives. Suggested introductory activities are not counted as numbered learning objectives.

Every official entry links to the original PDF page. Printed page numbers and physical PDF page numbers are distinguished. PDF text extraction cannot reproduce all typeset diagrams, chemical structures or typography, so the source PDF remains available for those details. Two spatial fraction expressions, in 5.14 and 13.17, have readable linear renderings checked visually against the PDF; the original extracted wording is retained separately.

**Scope:** coverage is tied to the supplied Issue 3 document. It does not claim to incorporate later Pearson amendments or establish learner mastery. Check the appropriate specification issue for your exam year with your teacher. The teacher-assessed Practical Endorsement is separate from this personal tracker.

## Study features

- Search all 19 topic areas and filter by year, strand or progress.
- Track Not started / Learning / Confident / Exam ready.
- Record notes, exam-question evidence, marks and mistakes.
- Schedule reviews: Learning → today, Confident → 7 days, Exam ready → 21 days. Review buttons offer 1, 7 or 21 days and record the review date.
- Track a whole objective and each explicit sub-point separately. Marking a parent ready does not automatically mark its children ready.
- Add missing/custom objectives or appendix requirements manually.
- Keep personal source-check flags distinct from the source provenance and learning progress. Official entries start with no learner source checks or mastery claims.
- Export and restore validated JSON backups.
- Use keyboard-accessible dialogs and a responsive mobile layout.

The percentage counts checklist entries, including both whole objectives and explicit sub-points. It is a self-assessment of these entries, not a predicted exam grade or a count of distinct exam questions.

## Existing progress and source updates

New browser sessions start with the official checklist. If this browser already has a starter or custom checklist, it is **not silently overwritten**. Select **Use official checklist**, inspect the explanation, then confirm. The previous checklist and progress are kept in an exportable archive; practical records and matching official-reference records are retained. Mastery on starter summaries is not guessed or transferred to different objectives.

The previous checklist can be exported from **Specification & backup**, and restored as a normal backup. Complete backups also include that archive.

Importing this exact uploaded PDF recognises its hash and offers the official checklist migration. Unknown 9CH0 PDFs still produce **draft extractions** requiring a full manual comparison. Those draft imports replace topic prompts after preview and acknowledgement, retain practical/maths entries, and do not transfer mastery between different IDs. Export a backup before importing a different issue.

## Data and privacy

When using plain `server.py` or GitHub Pages, checklist data stays in localStorage in the current browser origin. The updated `run_local.py` launcher additionally persists the checklist and work in the local study folder described below. There is no account, database, analytics, external AI service or automatic device sync. A different browser, device, hostname or port has separate storage. Export backups regularly; clearing browser data removes local progress.

Uploaded PDFs are processed by `pdftotext` on this app's server in a temporary directory and deleted afterwards. The bundled source PDF is intentionally retained as a reference. This is a local development server without production authentication; public hosting needs its own deployment configuration.

## Rebuild and verify

Regenerate the source-backed dataset and coverage audit:

```sh
python3 scripts/build_spec.py
```

This reads `app/specification.pdf`, uses no network, and fails if the audited topic counts, 205 sub-points, 16 core practical entries or 21 maths codes change unexpectedly. Generated data is in `app/official-data.json` and `app/official-data.js`. The source PDF is treated as data, never as agent or setup instructions.

Run the standard-library unit, source-coverage and grading checks:

```sh
python3 -m unittest discover -s tests -v
```

These check the actual PDF's identity, independently count the source's numbered objectives, check all topic endpoints, explicit sub-points, practical/maths coverage, footers, previously missed numbering and retained conditions.

With the app running, Python Playwright and `/usr/bin/chromium` available:

```sh
python3 tests/browser_smoke.py
```

The browser smoke test uses an isolated disposable context and writes fixtures/screenshots to `/tmp/element-tests`. It checks filters, progress persistence, safe evidence handling, source checks, review scheduling, practical records, backup round trip and invalid input, mobile layout, manual additions, synthetic PDF import, and the progress-preserving official-checklist migration and archive export.

## GitHub Pages hosting

The workflow in `.github/workflows/pages.yml` validates the checklist, publishes
only the `app` folder, and deploys on pushes to `main` or manual runs.

1. In the GitHub repository, open **Settings → Pages**.
2. Set **Source** to **GitHub Actions**. Your account/repository must support Pages.
3. Open **Actions → Deploy chemistry tracker to GitHub Pages → Run workflow**
   if the initial push ran before Pages was enabled.
4. When deployment succeeds, open the website URL shown under **Settings → Pages**.

The expected project URL is `https://ohiomonster57.github.io/A-level-Chem/`;
it is live only after a successful deployment. All app assets and source PDF links
are relative, so they work under the repository path.

GitHub Pages hosts static files and cannot run the Python PDF importer. The
workflow enables hosted mode in its output artifact; the UI explains that PDF
import needs the local app. The complete bundled checklist, progress, notes,
revision queue, practical records and JSON backup import/export work on Pages.
No API keys or additional repository secrets are required by this workflow.

Progress is stored in your browser for the hosted site's origin. It does not
sync automatically with your locally run copy; export and restore a JSON backup
to transfer progress. Repository visibility and Pages settings are managed in GitHub.

## Photo marking and question history

Open **Marked work** to upload up to six photographs of completed work or use a
phone camera. The app resizes images (up to 2000 pixels on the longest edge),
removes the original image metadata through canvas encoding, and stores the photos
in this browser's **IndexedDB** on the hosted website, or as real files in the selected study folder when using the updated local launcher. Uploads remain available before AI is connected.

With a configured backend, **Read & mark these photos** sends only that upload to
the AI provider after explicit consent. Marking identifies questions/subparts,
transcribes answers, maps them to the bundled 9CH0 references, and returns crop
rectangles for the relevant question/answer areas. Mixed-topic work appears under
each assigned topic; users can adjust crops, topic shares and objective references.
The whole original photo is retained so crops can be checked in context.

Each readable question gets a provisional percentage, based on chemical accuracy,
completeness, reasoning/working and relevant notation/units/precision. The four
rubric allocations total 100; the server calculates the score from the individual
awarded points, rather than trusting a model-generated total. Weighting adapts to
question type and is visible in the assessment. Feedback includes corrections and
skills to practise. Important unreadable/missing information and confidence below
0.65 are flagged **without a grade**, rather than marked wrong. AI markings may be
incorrect and are never represented as official marks or grade boundaries.

**Review before counting:** every result starts pending. Check the transcription,
original photo, crops and topic mapping, then select **Accept checked assessment**.
Flag incorrect readings instead of accepting a score for the wrong transcription.
Checklists' self-assessed mastery statuses do not change automatically.

### History, estimates and backups

The hosted app retains uploads/attempts in browser IndexedDB; the local launcher retains them in its study folder and reloads them independently of browser cache.
Accepted work contributes to a percentage evidence score and feedback panel on each
topic. This is separate from the manual study checklist. Scores weight recency
(90-day half-life), difficulty (1 / 1.25 / 1.5), reading confidence and the topic's
allocation. The score of a mixed-topic question is shared evidence, not an
independent mark for each topic. Where normalised question transcriptions match
exactly, the latest accepted attempt is used in the score; older attempts remain
visible in history. This matching is approximate in the educational sense: OCR
wording differences may prevent a repeat from being recognised.

Feedback summarises per-dimension scores and recurring practice areas from that
accepted evidence. Coverage counts distinct main specification objectives, and
labels limited/some/broader evidence based on question count and coverage. These
heuristics are transparent in the UI; the score is not a whole-topic mastery claim,
confidence interval, calibrated exam grade or prediction. The model does not have
an independent persistent memory; your saved history drives the topic aggregation.

Use **Export work history** for a JSON backup including the photos and assessments. In local folder mode, backing up the entire study folder also preserves the records and actual image files.
The existing **Export backup** button backs up the checklist only. Work-history
restore validates the whole file and merges new upload IDs without overwriting
existing IDs. The backend address is stored locally; its access token is
session-only, excluded from every backup. Uploaded work is not committed to GitHub
or automatically synced across devices. Export backups regularly because browser
storage can be cleared or evicted. Delete upload removes that upload and its
assessments from the browser and recalculates evidence; exported backup files are
not automatically deleted.

### API access: ChatGPT versus the website

A ChatGPT subscription, a custom GPT or a ChatGPT plugin **does not supply API
access to this website**. Automatic photo reading and marking uses a separate
OpenAI API account with model access and API billing. The default model is
`gpt-4.1`, configurable on the backend with `STUDY_AI_MODEL`.

**Never put an OpenAI API key in GitHub Pages, browser code, this chat, a work
backup, or a committed `.env` file.** The Python server reads `STUDY_AI_API_KEY`
(or an existing `OPENAI_API_KEY`) from its server environment. It calls the OpenAI
Responses API with image inputs and a strict JSON schema, with `store: false`.
That setting is not a claim of zero provider retention; provider data policies still
apply. The remotely hosted AI gateway does not write photos/prompts/responses to disk or application logs. The local edition intentionally writes study records, originals and crops to its chosen folder; API keys are never saved there. For remote requests, photos and returned marking exist transiently during the request.
Normal HTTP access logging includes paths/statuses, not request bodies/tokens.

### Connect the hosted website to a private backend (Render)

The backend files are supplied, but deployment and real API credentials are **not
created automatically** by the GitHub Pages workflow. Hosting and API usage may
incur separate charges depending on the plans you choose.

1. Sign in to [Render](https://render.com/) and choose **New → Blueprint**.
2. Connect `OhioMonster57/A-level-Chem` and choose `render.yaml` from `main`.
3. In Render's secure environment-variable configuration, enter your OpenAI key
   as **STUDY_AI_API_KEY**. Do not commit the value to the repository.
4. Render generates **STUDY_ACCESS_TOKEN**. Keep it private; it authenticates your
   browser to the backend and is different from your OpenAI API key.
5. **STUDY_ALLOWED_ORIGIN** is set to `https://ohiomonster57.github.io`. If the
   website has a different origin, change it to the exact origin (scheme + host,
   without a path). Multiple trusted origins can be comma-separated. CORS alone
   is not authentication; the access token is always required for marking.
6. Deploy the service. Copy its HTTPS service URL, such as
   `https://your-service.onrender.com`, and its generated access token.
7. On the chemistry website, open **Marked work → Connect marking backend**.
   Enter that URL and **backend access token**, then check/save the connection.
   Do not enter the OpenAI API key into this form.
8. Upload a clear completed question, confirm the photo-sharing consent checkbox,
   and select **Read & mark these photos**. Review the result before accepting it.

The server refuses marking when credentials/authentication are missing, rejects
unapproved browser origins, allows only one in-flight assessment per instance and
limits each running instance to 12 marking sessions/hour. The hourly limit resets
on restart and is not a provider-wide spending cap; set a budget/usage controls in
your API account. For shared or multi-user hosting, replace the single access token
and per-instance rate limit with per-user authentication and shared quotas.

For local use, set the same server environment variables securely and run
`python3 server.py`. The default frontend backend address is the local origin.
The API routes are `/api/health` and `/api/mark-work`; neither is implemented by
GitHub Pages itself. The Docker image runs as a non-root user and honours `PORT`.

### Marking validation

`python3 -m unittest discover -s tests -v` now includes gateway auth/CORS tests,
server-side score recomputation, invalid crops/references/weights, uncertainty
handling, and mocked provider requests. `python3 tests/work_smoke.py`, with the
local app running, tests photo persistence, consent, session connection, **mocked**
AI replies, crops, review, mixed-topic scoring, backups, repeat-attempt history,
flags and mobile layout. It makes no real AI calls or API charges.

Live AI quality/accuracy, a production Render deployment and real-credential
connectivity remain unverified until an actual backend is deployed and configured.
The UI explicitly shows this prerequisite instead of generating simulated grades.

## One-computer local edition

Download/extract the repository ZIP and read [LOCAL-START-HERE.md](LOCAL-START-HERE.md).
Run **START-WINDOWS.cmd** on Windows or `python3 run_local.py` on Mac/Linux. The
launcher securely prompts for an API key, generates a per-run backend token, binds
only to 127.0.0.1, and opens the local browser with automatic backend connection.
It never saves the API key to disk. No Render deployment or extra Python packages
are needed for photo marking. `pdftotext` remains optional for importing a different
specification PDF. Live provider marking still depends on a valid key, model access
and API billing; all grading remains provisional.

## Folder persistence, topic libraries and progress charts

The local launcher defaults to `~/Documents/Element-Chemistry` and supports
`--data-dir`. It checks that the directory is writable before opening the app.
Local-only authenticated routes persist complete records atomically, save actual
uncropped uploaded photo files (the app-resized copies), and write question JSON/cropped JPEGs under `topics/topic-NN`.
Mixed-topic questions appear in each mapped topic. Browser work can be copied to
the folder through the migration button; browser originals are not removed.

Checklist changes are also mirrored to `checklist.json`. On startup, the saved
folder checklist is loaded in a fresh browser. A newer timestamped browser copy
can be recovered to the folder; differing previous checklist copies are preserved
under `backups`. No credentials are included in those records. Hosted GitHub Pages
continues to use browser storage, not the local filesystem.

Each topic now has a question library showing every saved attempt and its crop,
score/review status and feedback. The overview charts show the four manual
confidence states, their distribution across topics, and coverage of main
objectives by accepted question evidence. Self-assessment, evidence coverage and
AI score are distinct measures.

Marking uses XMLHttpRequest to show actual upload byte progress where available,
then an indeterminate waiting indicator and elapsed time. It never invents an AI
completion percentage. Saving crops/records is a separate visible phase. Errors
and successful result counts remain on the page until dismissed, as well as being
stored on the upload. No analysis output means no fabricated score.

`tests/disk_work_smoke.py` verifies originals/crops on disk, progress/error UI,
topic library, confidence charts, and restoration after both a process restart
and a new browser context. Its provider replies are explicitly mocked. Live AI
quality still requires a real configured account and remains provisional.

## Topic Weakness review

A **Weakness** button sits beside each topic's library/history controls. It opens
an offline review built from accepted, readable question assessments for that topic:
linked specification points, lower-scoring rubric dimensions, recorded mistakes,
corrections, question links and subject-specific knowledge tips. No new API request
or charge is made. Pending/flagged work is excluded. The latest accepted attempt of
an exactly matching question drives current priorities; previous accepted attempts
remain available and improvements are identified separately.

Revision priority uses a latest question score below 85% or an applicable rubric
dimension below 80%. These are study heuristics, not grade boundaries or a
whole-topic diagnosis. Mixed-topic/multi-objective marks remain shared evidence.
When there is no accepted evidence, the dialog says so rather than inventing
weaknesses. When no latest attempt meets the low-score criteria, it points to
uncovered objectives instead of claiming complete mastery. Tips are curated
chemistry guidance selected using the question context and saved feedback, not a
new AI-generated diagnosis; verify saved AI corrections against trusted notes.
