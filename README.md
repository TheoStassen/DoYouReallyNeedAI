# DoYouReallyNeedAI — Web app

A small Flask-based web application that helps you quickly check whether a project / idea needs AI. The app uses a file-backed question/answer store (JSON) and provides a modern dark-first UI to search questions and view answers — including embedded charts for demo answers.

Key points
- No external database required: sample data is stored in `example_qa_store.json`.
- Modern, responsive UI built with Tailwind CSS (via CDN) and Chart.js for simple plots.
- Dark mode is supported (dark by default) and can be toggled in the header.

Quick start (local)

1. Create a virtual environment and install dependencies from `requirements.txt` (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the Flask app (project uses `app.py`):

```bash
# start directly
python3 app.py
```

3. Open the UI at: http://127.0.0.1:5000/

Project layout (important files)
- `app.py` — Flask application entry point and HTTP routes (API endpoints such as `/api/search`, `/api/answer-data`).
- `templates/index.html` — main UI template (contains the search form, result rendering, spinner and the fixed credits bar). Edit this file to change layout or visual content.
- `static/js/chart-helper.js` — client-side helper to fetch chart data and render using Chart.js.
- `example_qa_store.json` — file-backed QA store used by the app for questions and answers (sample data).
- `qa_store.py`, `qa_models.py` — local Python helpers/models that manipulate the JSON QA store.
- `requirements.txt` — Python dependencies used by the project.

Editing questions & answers
- The QA data lives in `example_qa_store.json`. Each question can link to multiple answers and answers can be shared.
- To add or edit questions/answers, edit the JSON file directly or use the helper functions in `qa_store.py` and `qa_demo.py` as examples.
- Answers can contain special markers (for UI formatting): the app splits answer text on `#` to separate a title from the paragraph.

Charts & demonstration answers
- Certain answers are special and will trigger a chart rendering (the frontend fetches `/api/answer-data` for them).
- For testing, one sample answer id returns random x/y data so you can see how charts render inside an answer card.

Deployment notes
- The project includes a `Dockerfile` and an `entrypoint.sh` so it can be containerized. If you deploy with the container, ensure the environment provides the right runtime (Python, any required system packages) and that the `gunicorn` binary is available if you use it in the entrypoint.
- Fly.io is a simple option for deploying containerized Python apps (small free tier available). Heroku-style PaaS also works.
- If your production environment must call the Copilot CLI, be aware that Copilot CLI authentication may require interactive login and/or tokens — containerized non-interactive login needs secrets or a pre-authenticated token. Test the CLI flow in your target environment before relying on it in production.

Customization & theme
- The UI uses Tailwind via CDN to keep the project light. If you need to customize the theme further, edit `templates/index.html` and the inline styles.
- Credits/contact are displayed in a fixed bottom bar; you can edit contact details directly in `templates/index.html`.

Troubleshooting
- If charts don't appear: open the browser console to check for failed `/api/answer-data` requests or JS errors. Ensure `chart-helper.js` is loaded and Chart.js CDN is reachable.
- If the theme doesn't toggle correctly, clear site storage (localStorage) or check that the `.dark` class is applied to the `<html>` element.

License & credits
- This project is a prototype meant for experimentation and UI design. Replace the placeholder contact/github links in the credits bar with your real details.

Contact
- Author: Your Name Here — replace contact details in `templates/index.html`.

Enjoy — and if you want, I can:
- extract the credits block into a reusable template partial (`_credits.html`),
- move external vendor scripts (Chart.js) to `static/` to avoid CDN warnings, or
- add a small management page to edit `example_qa_store.json` from the web UI.
