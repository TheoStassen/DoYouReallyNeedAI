import time

from flask import Flask, jsonify, request, render_template
import os
import numpy as np
from qa_store import QuestionAnswerStore

# call copilot queries for debugging (non-blocking safely)
try:
    from copilot_use import copilot_query
except Exception:
    copilot_query = None

BASE_DIR = os.path.dirname(__file__)
STORE_PATH = os.path.join(BASE_DIR, "data/qa_store.json")

app = Flask(__name__, template_folder="templates")
store = QuestionAnswerStore(STORE_PATH)

# Configure logging so debug messages are visible both in dev and under gunicorn
import logging
import sys
loglevel_name = os.environ.get('LOGLEVEL', 'DEBUG').upper()
loglevel = getattr(logging, loglevel_name, logging.DEBUG)

# If running under Gunicorn, reuse its error handlers so logs go to the same place
gunicorn_logger = logging.getLogger('gunicorn.error')
if getattr(gunicorn_logger, 'handlers', None):
    handlers = gunicorn_logger.handlers
    # ensure handlers use requested level
    for h in handlers:
        try:
            h.setLevel(loglevel)
        except Exception:
            pass
    app.logger.handlers = handlers
    app.logger.setLevel(loglevel)
    app.logger.propagate = False
    logging.getLogger('werkzeug').handlers = handlers
    logging.getLogger('werkzeug').setLevel(loglevel)
else:
    # Standalone: ensure there's a StreamHandler to stdout
    root = logging.getLogger()
    root.setLevel(loglevel)
    # prefer an existing StreamHandler to stdout if available
    found = False
    for h in list(root.handlers):
        if isinstance(h, logging.StreamHandler) and getattr(h, 'stream', None) in (sys.stdout, sys.stderr, None):
            found = True
            h.setLevel(loglevel)
            break
    if not found:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(loglevel)
        fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
        sh.setFormatter(fmt)
        root.addHandler(sh)
    app.logger.setLevel(loglevel)
    app.logger.propagate = True
    logging.getLogger('werkzeug').setLevel(loglevel)

# --- New: fast local matcher using TF-IDF + cosine similarity ---
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

# Prepare data for vectorizer
_question_ids = []
_question_texts = []
for qid, qobj in store._data.get('questions', {}).items():
    _question_ids.append(qid)
    _question_texts.append((qobj.get('text') or '').strip())

_vectorizer = None
_question_tfidf = None
if SKLEARN_AVAILABLE and _question_texts:
    try:
        _vectorizer = TfidfVectorizer(stop_words='english')
        _question_tfidf = _vectorizer.fit_transform(_question_texts)
        app.logger.debug('Built TF-IDF matrix for %d questions', len(_question_texts))
    except Exception:
        _vectorizer = None
        _question_tfidf = None

# Small LRU cache for Copilot responses to avoid repeating expensive calls
from functools import lru_cache

@lru_cache(maxsize=512)
def _cached_copilot(prompt: str) -> str:
    if not copilot_query:
        return ''
    return copilot_query(prompt)


@app.route("/api/search")
def api_search():
    starting_time = time.time()
    start_search_time = time.time()
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    app.logger.debug("Search query received: %r", q)
    results = []

    # Quick exact-id shortcut
    if q.isdigit() and q in store._data.get("questions", {}):
        qobj = store._data["questions"][q]
        results.append({
            "id": q,
            "text": qobj.get("text", ""),
            "description": qobj.get("description", ""),
            "answers": store.get_answers_for_question(q),
        })
        app.logger.debug(f'question id exact match found : {qobj}', )
        return jsonify(results)

    # Simple substring search
    qlow = q.lower()
    for qid, qobj in store._data.get("questions", {}).items():
        text = (qobj.get("text") or "").strip()
        if qlow in text.lower():
            results.append({
                "id": qid,
                "text": text,
                "description": qobj.get("description", ""),
                "answers": store.get_answers_for_question(qid),
            })
    if results:
        app.logger.debug('search time first part (substring): %.3f sec', time.time() - start_search_time)
        return jsonify(results)
    #
    # # If sklearn is available, use the local TF-IDF matcher first (fast)
    # if SKLEARN_AVAILABLE and _vectorizer is not None and _question_tfidf is not None:
    #     try:
    #         vec = _vectorizer.transform([q])
    #         # cosine similarity via linear_kernel is fast for sparse matrices
    #         sims = linear_kernel(vec, _question_tfidf).flatten()
    #         # Get top-3 candidates from TF-IDF sims (highest scores)
    #         top_k = 3
    #         if sims.size > 0:
    #             top_idx = list(np.argsort(sims)[-top_k:][::-1])
    #         else:
    #             top_idx = []
    #         app.logger.debug('Local matcher top indices: %s', top_idx)
    #         # Add any candidate with score >= 0.5 to results
    #         added = 0
    #         for idx in top_idx:
    #             score = float(sims[int(idx)])
    #             qid = _question_ids[int(idx)]
    #             app.logger.debug('Candidate qid=%s score=%.4f', qid, score)
    #             if score >= 0.3:
    #                 qobj = store._data['questions'][qid]
    #                 results.append({
    #                     'id': qid,
    #                     'text': qobj.get('text', ''),
    #                     'answers': store.get_answers_for_question(qid),
    #                 })
    #                 added += 1
    #         if added:
    #             app.logger.debug('Returning %d local TF-IDF matches (threshold 0.5)', added)
    #             return jsonify(results)
    #     except Exception:
    #         app.logger.exception('Local TF-IDF match failed')

    app.logger.debug("search time first part: %.2f seconds", time.time() - start_search_time)

    # If Copilot is available, call it as a fallback. Use cached results and simpler prompts.
    if copilot_query:
        try:
            # First, use a short summarization prompt (fast response expected)
            start_query_time = time.time()
            # Simplify prompt; avoid large instructions or mentioning filenames — keep it short and focused
            summary_prompt = f"En une courte phrase (3 mots max), résume la question correspondant à: {q}"
            q_summary = _cached_copilot(summary_prompt).split("\n")[-1].strip()
            app.logger.debug("search time first query: %.2f seconds", time.time() - start_query_time)
            app.logger.debug("Copilot response summary for prompt %r: %s", q, str(q_summary))

            if q_summary:
                for qid, qobj in store._data.get("questions", {}).items():
                    text = (qobj.get("text") or "")
                    if q_summary.lower() in text.lower():
                        results.append({
                            "id": qid,
                            "text": text,
                            "description": qobj.get("description", ""),
                            "answers": store.get_answers_for_question(qid),
                        })
                if results:
                    app.logger.debug('Found matches using copilot summary')
                    return jsonify(results)

            # Fallback: ask Copilot to return the best matching ID.
            start_sec_query_time = time.time()
            # Make prompt compact: only provide top-K candidates (ids + short text) for Copilot to choose from.
            # This greatly reduces Copilot work vs giving it the whole store or a large prompt.
            app.logger.debug("Copilot response %r did not match any questions",
                             q_summary)
            query_text = f"Examine data/qa_store.json, get the question that is the most similar to this : ' {q_summary} ', the response to this query must be only the question ID, nothing else."
            q_id = copilot_query(query_text).split("\n")[-1].strip()
            app.logger.debug("search time second copilot query: %.2f seconds",
                             time.time() - start_sec_query_time)
            app.logger.debug("Copilot returned question id %r for prompt %r",
                             q_id, q)
            if q_id.isdigit() and q_id in store._data.get("questions", {}):
                qobj = store._data["questions"][q_id]
                results.append({
                    "id": q_id,
                    "text": qobj.get("text", ""),
                    "description": qobj.get("description", ""),
                    "answers": store.get_answers_for_question(q_id),
                })
            else:
                app.logger.debug(
                    "Copilot returned invalid question id %r for prompt %r",
                    q_id, q)

            app.logger.debug('search time for copilot query: %.2f seconds', time.time() - starting_time)
            return jsonify(results)

        except Exception as e:
            app.logger.exception("copilot_query failed for prompt %r: %s", q, e)

    # final fallback: empty
    return jsonify([])


@app.route('/api/answer-data/<answer_id>')
def api_answer_data(answer_id):
    # For testing: when answer_id == '4' return 10 random x/y points
    if answer_id == '3':
        xs = list(range(1, 1001))
        len_xs = len(xs)
        ys = [ 100 * np.log10(x) / np.log10(len_xs)  for x in xs]
        return jsonify({"x": xs, "y": ys})
    return jsonify({"error": "no data for this answer"}), 404


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    # Simple local server for development
    app.run(debug=True, host="127.0.0.1", port=5000)
