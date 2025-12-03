#!/usr/bin/env python3
"""Extract question texts from qa_store.json and write one question per line to a text file.

Usage:
    python transform_json_into_txt.py [output_path]

If no output_path is provided, writes to data/questions.txt (same folder).
The script is robust to a leading comment line(s) starting with '//' in the JSON file (the repo's qa_store.json contains such a line).
"""

from pathlib import Path
import json
import sys

def load_json_allowing_comments(path: Path):
    """Load JSON file while ignoring lines that start with '//' (comments).

    Returns parsed JSON object.
    """
    text = path.read_text(encoding="utf-8")
    # remove lines that start with // (common in these repo JSONs)
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("//")]
    clean = "\n".join(lines)
    return json.loads(clean)


def extract_question_texts(qa_data: dict):
    """Return a list of question texts in ascending numeric key order."""
    questions = qa_data.get("questions") or {}
    # sort keys by integer value when possible
    try:
        sorted_items = sorted(questions.items(), key=lambda kv: int(kv[0]))
    except Exception:
        sorted_items = list(questions.items())
    texts = []
    for _k, q in sorted_items:
        t = q.get("text") if isinstance(q, dict) else None
        if t:
            # normalize whitespace and remove newlines
            texts.append(" ".join(str(t).split()))
    return texts


def write_lines(path: Path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")


def main(argv):
    script_dir = Path(__file__).parent
    qa_path = script_dir / "qa_store.json"
    default_out = script_dir / "questions.txt"
    out_path = Path(argv[1]) if len(argv) > 1 else default_out

    if not qa_path.exists():
        print(f"Error: expected {qa_path} to exist", file=sys.stderr)
        return 2

    try:
        data = load_json_allowing_comments(qa_path)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return 3

    texts = extract_question_texts(data)
    write_lines(out_path, texts)
    print(f"Wrote {len(texts)} questions to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
