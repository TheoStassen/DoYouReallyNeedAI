import time

from flask import Flask, jsonify, request, render_template
import os
import numpy as np
from qa_store import QuestionAnswerStore

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

# --- New: fast semantic matcher using Sentence-Transformers (SBERT) ---
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    SBERT_AVAILABLE = True
except Exception:
    SBERT_AVAILABLE = False

# Prepare data for semantic search
_question_ids = []
_question_texts = []
for qid, qobj in store._data.get('questions', {}).items():
    _question_ids.append(qid)
    # Combine text and description for richer semantic matching
    text = (qobj.get('text') or '').strip()
    desc = (qobj.get('description') or '').strip()
    combined = f"{text}. {desc}" if desc else text
    _question_texts.append(combined)

_sbert_model = None
_question_embeddings = None
if SBERT_AVAILABLE and _question_texts:
    try:
        # Use a lightweight multilingual model that works well for French & English
        # 'paraphrase-multilingual-MiniLM-L12-v2' is ~420MB, fast, and accurate
        # Alternative: 'all-MiniLM-L6-v2' (English only, smaller ~80MB)
        _sbert_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        _question_embeddings = _sbert_model.encode(_question_texts, convert_to_tensor=True, show_progress_bar=False)
        app.logger.info('Built SBERT embeddings for %d questions', len(_question_texts))
    except Exception as e:
        app.logger.exception('Failed to build SBERT embeddings: %s', e)
        _sbert_model = None
        _question_embeddings = None

# Small LRU cache for query embeddings to avoid recomputing for repeated queries
from functools import lru_cache

@lru_cache(maxsize=512)
def _get_cached_embedding_tuple(query: str):
    """Cache embeddings for repeated queries. Returns tuple for hashability."""
    if _sbert_model is None:
        return None
    emb = _sbert_model.encode(query, convert_to_tensor=True, show_progress_bar=False)
    return emb


def semantic_search_questions(query: str, top_k: int = 5):
    """
    Find the most semantically similar questions using SBERT embeddings.

    Strategy:
    - If there's a match > 0.7 and next result is < 0.7: return only that match
    - If multiple results between 0.5 and 0.7: return up to 3 best in that range
    - If no result >= 0.5: return the single best match regardless of score

    Returns list of (question_id, similarity_score) tuples.
    """
    HIGH_THRESHOLD = 0.7
    MID_THRESHOLD = 0.5

    if _sbert_model is None or _question_embeddings is None:
        return []

    query_embedding = _get_cached_embedding_tuple(query)
    if query_embedding is None:
        return []

    # Compute cosine similarities
    cos_scores = st_util.cos_sim(query_embedding, _question_embeddings)[0]

    # Get top-k results sorted by score
    top_results = cos_scores.topk(k=min(top_k, len(_question_ids)))

    # Build list of (qid, score)
    all_matches = []
    for score, idx in zip(top_results.values, top_results.indices):
        all_matches.append((_question_ids[int(idx)], float(score)))

    if not all_matches:
        return []

    # Strategy 1: Check if top match is > 0.7 and second is < 0.7
    if all_matches[0][1] > HIGH_THRESHOLD:
        if len(all_matches) == 1 or all_matches[1][1] < HIGH_THRESHOLD:
            # Unique high-quality match - return only this one
            return [all_matches[0]]

    # Strategy 2: Get all matches between 0.5 and 0.7 (or above)
    mid_range_matches = [(qid, score) for qid, score in all_matches if score >= MID_THRESHOLD]
    if mid_range_matches:
        # Return up to 3 best matches in this range
        return mid_range_matches[:3]

    # Strategy 3: No match >= 0.5, return the single best match
    return [all_matches[0]]


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


    app.logger.debug("search time first part: %.2f seconds", time.time() - start_search_time)

    # Use fast SBERT semantic search as fallback
    if SBERT_AVAILABLE and _sbert_model is not None:
        try:
            start_semantic_time = time.time()
            semantic_results = semantic_search_questions(q, top_k=5)
            app.logger.debug("SBERT semantic search took: %.3f seconds", time.time() - start_semantic_time)

            for q_id, score in semantic_results:
                if q_id in store._data.get("questions", {}):
                    qobj = store._data["questions"][q_id]
                    results.append({
                        "id": q_id,
                        "text": qobj.get("text", ""),
                        "description": qobj.get("description", ""),
                        "answers": store.get_answers_for_question(q_id),
                        "similarity_score": round(score, 3),
                    })
                    app.logger.debug("Matched question id=%s with score=%.3f", q_id, score)

            if results:
                app.logger.debug('Total search time: %.3f seconds', time.time() - starting_time)
                return jsonify(results)
        except Exception as e:
            app.logger.exception("SBERT search failed: %s", e)

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
