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
- Photos, assessments and topic history remain in the current browser/device. The backend processes them transiently. Use **Export work history** to back up photos and grades, and **Export backup** for the separate checklist data.
- GitHub Pages and this local address have separate browser storage. Export from the old website and restore at the local one to transfer progress. Always use the same **127.0.0.1:3000** address and browser. `localhost`, a different port or a private/incognito window can have separate history.
- AI grading is provisional. Review it before accepting. Unclear questions should be rephotographed rather than treated as wrong.

## Optional features and troubleshooting

- The official checklist/PDF are bundled. Importing a *different* specification PDF additionally needs Poppler's `pdftotext`; photo marking does not.
- If port 3000 is occupied, stop the other app. `python3 run_local.py --port 3001` (Windows: `py -3 run_local.py --port 3001`) is also supported, but uses a separate browser origin/history.
- If the browser does not open automatically, visit the address printed by the launcher.
- If the key is rejected or usage is limited, check your OpenAI API project permissions/billing. This is separate from your ChatGPT subscription.
- The launcher requires a terminal capable of a hidden prompt. For a Python/Jupyter notebook, read the key securely with `getpass.getpass()` and pass it as a process environment variable to the launcher; do not place a literal key in a saved notebook cell.
