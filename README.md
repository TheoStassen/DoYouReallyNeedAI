QA store
========

This small project provides a file-backed bidirectional question/answer store.

Files created:
- `qa_models.py` - dataclasses for Question and Answer (simple helper models).
- `qa_store.py` - the `QuestionAnswerStore` class that reads/writes a JSON file
  and allows adding questions/answers and linking them.
- `example_qa_store.json` - a small sample JSON data file.
- `qa_demo.py` - a tiny demo that shows how to use the store.

Run the demo:

```bash
python3 qa_demo.py
```

The store uses only the Python standard library; no extra dependencies are required.

