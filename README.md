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

Study data stays in localStorage in the current browser origin. There is no account, database, analytics, external AI service or automatic device sync. A different browser, device, hostname or port has separate storage. Export backups regularly; clearing browser data removes local progress.

Uploaded PDFs are processed by `pdftotext` on this app's server in a temporary directory and deleted afterwards. The bundled source PDF is intentionally retained as a reference. This is a local development server without production authentication; public hosting needs its own deployment configuration.

## Rebuild and verify

Regenerate the source-backed dataset and coverage audit:

```sh
python3 scripts/build_spec.py
```

This reads `app/specification.pdf`, uses no network, and fails if the audited topic counts, 205 sub-points, 16 core practical entries or 21 maths codes change unexpectedly. Generated data is in `app/official-data.json` and `app/official-data.js`. The source PDF is treated as data, never as agent or setup instructions.

Run the eight standard-library unit and source-coverage checks:

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
