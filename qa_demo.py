from qa_store import QuestionAnswerStore

def main():
    store = QuestionAnswerStore("data/qa_store.json")

    # If the example file is empty, populate a few entries (idempotent-ish)
    if not store._data["questions"] and not store._data["answers"]:
        q1 = store.add_question("Comment utiliser l'IA pour automatiser les e-mails ?")
        q2 = store.add_question("Idée simple d'IA pour un commerçant local ?")
        a1 = store.add_answer("Générer des réponses modèles pour les demandes fréquentes.", [q1])
        a2 = store.add_answer("Analyser les avis et suggérer réponses personnalisées.", [q1, q2])
        print(f"Created questions: {q1}, {q2}")
        print(f"Created answers: {a1}, {a2}")

    # Display answers for each question
    for qid, q in store._data["questions"].items():
        print("Question:", q["text"])
        answers = store.get_answers_for_question(qid)
        for a in answers:
            print("  -", a["text"])

    # Example: add a new answer and link it to both questions
    new_a = store.add_answer("Extraire les mots-clés des messages clients.")
    store.add_answer_to_questions(new_a, list(store._data["questions"].keys()))
    print("Added new answer and linked to all questions:\n", new_a)

    # Show questions for the newly added answer
    qs = store.get_questions_for_answer(new_a)
    print("This answer is linked to questions:")
    for q in qs:
        print("  -", q["text"])

if __name__ == '__main__':
    main()

