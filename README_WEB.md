Simple Flask front-end to query the existing QA store (file-backed JSON).

Run (recommended inside a virtualenv):

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

Notes:
- The app reads `example_qa_store.json` using the existing `QuestionAnswerStore` class in `qa_store.py`.
- Search is a simple substring match over question text. You can type a numeric question id to get exact match by id.
- This is intentionally tiny and dependency-free for quick iteration. For production you'd add input sanitization, pagination, and a proper API and tests.

