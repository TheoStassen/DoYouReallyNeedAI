import json
import os
import uuid
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional

# File-backed bidirectional QA store.
# JSON layout:
# {
#   "questions": { "qid": {"text": "...", "answers": [aid, ...]}, ...},
#   "answers":   { "aid": {"text": "...", "questions": [qid, ...]}, ...}
# }

class QuestionAnswerStore:
    def __init__(self, path: str = "qa_store.json"):
        self.path = path
        self._data = {"questions": {}, "answers": {}}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                # If file is corrupted, start fresh but don't overwrite until save is called
                self._data = {"questions": {}, "answers": {}}

    def _save(self):
        # atomic write
        dirpath = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(dirpath, exist_ok=True)
        with NamedTemporaryFile("w", dir=dirpath, delete=False, encoding="utf-8") as tf:
            json.dump(self._data, tf, ensure_ascii=False, indent=2)
            tmpname = tf.name
        os.replace(tmpname, self.path)

    def add_question(self, text: str) -> str:
        # ID is the next question ID available
        qid = str(self._data["questions"].__len__() + 1)
        self._data["questions"][qid] = {"text": text, "description": text, "answers": []}
        self._save()
        return qid

    def add_answer(self, text: str, question_ids: Optional[List[str]] = None) -> str:
        # ID is the next question ID available
        aid = str(self._data["answers"].__len__() + 1)
        self._data["answers"][aid] = {"text": text, "questions": []}
        # Link after registering answer
        if question_ids:
            for qid in question_ids:
                self.link(aid, qid)
        else:
            self._save()
        return aid

    def link(self, answer_id: str, question_id: str):
        if question_id not in self._data["questions"]:
            raise KeyError(f"Unknown question id: {question_id}")
        if answer_id not in self._data["answers"]:
            raise KeyError(f"Unknown answer id: {answer_id}")

        q_list = self._data["questions"][question_id].setdefault("answers", [])
        a_list = self._data["answers"][answer_id].setdefault("questions", [])

        if answer_id not in q_list:
            q_list.append(answer_id)
        if question_id not in a_list:
            a_list.append(question_id)
        self._save()

    def add_answer_to_questions(self, answer_id: str, question_ids: List[str]):
        for qid in question_ids:
            self.link(answer_id, qid)

    def get_answers_for_question(self, question_id: str) -> List[Dict[str, str]]:
        if question_id not in self._data["questions"]:
            return []
        return [
            {"id": aid, "text": self._data["answers"][aid]["text"]}
            for aid in self._data["questions"][question_id].get("answers", [])
            if aid in self._data["answers"]
        ]

    def get_questions_for_answer(self, answer_id: str) -> List[Dict[str, str]]:
        if answer_id not in self._data["answers"]:
            return []
        return [
            {"id": qid, "text": self._data["questions"][qid]["text"], "description": self._data["questions"][qid].get("description", "")}
            for qid in self._data["answers"][answer_id].get("questions", [])
            if qid in self._data["questions"]
        ]

    def remove_link(self, answer_id: str, question_id: str):
        if question_id in self._data["questions"]:
            q_answers = self._data["questions"][question_id].get("answers", [])
            if answer_id in q_answers:
                q_answers.remove(answer_id)
        if answer_id in self._data["answers"]:
            a_questions = self._data["answers"][answer_id].get("questions", [])
            if question_id in a_questions:
                a_questions.remove(question_id)
        self._save()

