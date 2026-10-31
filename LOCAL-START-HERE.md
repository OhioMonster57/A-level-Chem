# Run Element Chemistry on your own computer

You need **Python 3.10 or later** and a modern browser. There are no pip/npm packages to install for the app or photo marking. Your own OpenAI API account needs API billing and access to the configured model (default: gpt-4.1).

## Windows

1. Extract the whole downloaded ZIP (do not run files inside the ZIP preview).
2. If needed, install Python 3 from https://www.python.org/downloads/windows/.
3. Double-click **START-WINDOWS.cmd** in the extracted folder.
4. Paste your OpenAI API key at the hidden prompt and press Enter. Nothing appears while you type/paste; this is intentional. Alternatively, press Enter without a key to use the tracker without automatic marking.
5. The browser opens automatically at **http://127.0.0.1:3000/#work**.
6. Upload your completed work, confirm photo-sharing consent and choose **Read & mark these photos**. Check the transcription/crops and accept the assessment before it affects your topic estimate.
7. Keep the terminal window open. Press **Ctrl+C** there to stop the app.

If double-clicking the launcher does not work, open a terminal in this folder and run:

```bat
py -3 run_local.py
```

## Mac or Linux

Open a terminal in the extracted folder and run:

```sh
python3 run_local.py
```

On macOS you can also use START-MAC.command if the downloaded file is executable. If your operating system prevents opening it, use the terminal command instead of disabling security settings.

## What stays private and what needs the internet

- Your API key is read through a hidden prompt and kept in the running Python process. The launcher never saves it to a file, a notebook, browser storage, or GitHub. Restarting asks for it again. An existing STUDY_AI_API_KEY or OPENAI_API_KEY process environment variable is reused without printing it.
- The local server listens only on **127.0.0.1**, not your Wi-Fi/network address. A temporary backend access token is generated and automatically connected to the local browser; it is not your OpenAI API key.
- The website does not need Render, a hosted backend or a ChatGPT plugin. Internet access is still required when sending photos to OpenAI. API usage is billed separately from ChatGPT.
- The updated local launcher saves originals, question crops, assessments and the checklist as real files under **%USERPROFILE%\Documents\Element-Chemistry** on Windows (or **~/Documents/Element-Chemistry** on Mac/Linux). The exact path is printed in the terminal and shown on the Marked work page. These files survive browser-data clearing and app upgrades. Export backups or copy this whole data folder for additional protection.
- To bring existing local IndexedDB work into the folder, select **Copy previous browser history to folder** on Marked work. Browser originals are kept. For GitHub Pages work, export there and restore in the local app. The updated launcher loads its folder data even in a fresh browser; the access token is still connected separately for each session.
- AI grading is provisional. Review it before accepting. Unclear questions should be rephotographed rather than treated as wrong.

## Optional features and troubleshooting

- The official checklist/PDF are bundled. Importing a *different* specification PDF additionally needs Poppler's `pdftotext`; photo marking does not.
- If port 3000 is occupied, stop the other app. `python3 run_local.py --port 3001` (Windows: `py -3 run_local.py --port 3001`) is also supported, but still loads your study data from the same folder.
- If the browser does not open automatically, visit the address printed by the launcher.
- If the key is rejected or usage is limited, check your OpenAI API project permissions/billing. This is separate from your ChatGPT subscription.
- The launcher requires a terminal capable of a hidden prompt. For a Python/Jupyter notebook, read the key securely with `getpass.getpass()` and pass it as a process environment variable to the launcher; do not place a literal key in a saved notebook cell.

## Your local folder and question library

Default Windows location: `%USERPROFILE%\Documents\Element-Chemistry`.

```text
Element-Chemistry/
  checklist.json                      confidence, notes and checklist progress
  uploads/<upload-id>/record.json      complete work/assessment record
  uploads/<upload-id>/originals/       uncropped uploaded photos (resized copies)
  topics/topic-01/<upload-id>/         cropped question images and question JSON
  topics/topic-02/<upload-id>/         …one folder for each mapped topic…
  backups/                            preserved differing browser checklist copies
```

Mixed-topic questions have crop/feedback files in each mapped topic folder. The
record JSON also retains the saved photo data so it can reconstruct the in-app
library. Do not remove these records if you want to keep the library. Delete work
through the app, or back up the entire folder before making manual changes.

Choose another folder by running:

```bat
py -3 -X utf8 run_local.py --data-dir "D:\ChemistryStudy"
```

The dashboard shows checklist confidence, confidence by topic and objective
coverage from accepted question assessments. Each topic has a question library
including previous attempts, crops and feedback.

While marking, a visible progress panel shows actual upload progress when the
browser provides it, then an indeterminate waiting bar and elapsed time. The AI
provider does not expose a trustworthy completion percentage. A persistent success
or error message appears afterwards. If you still get no assessment, copy that
error message (not your key) for diagnosis. A valid key, model access, API billing
and internet access are still required for live grading.
