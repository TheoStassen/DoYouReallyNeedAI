#!/usr/bin/env python3
"""
Script to check bidirectional consistency in qa_store.json.
For each answer, verifies that all linked questions have that answer in their .answers list.

Usage:
    python check_qa_consistency.py          # Check only
    python check_qa_consistency.py --fix    # Check and fix errors
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(__file__)
STORE_PATH = os.path.join(BASE_DIR, "data/qa_store.json")


def main():
    fix_mode = '--fix' in sys.argv

    print("=" * 60)
    print("QA Store Bidirectional Consistency Check")
    if fix_mode:
        print("MODE: FIX (will repair errors)")
    else:
        print("MODE: CHECK ONLY (use --fix to repair)")
    print("=" * 60)

    # Load the store
    if not os.path.exists(STORE_PATH):
        print(f"ERROR: {STORE_PATH} not found!")
        return

    with open(STORE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions = data.get('questions', {})
    answers = data.get('answers', {})

    print(f"Loaded {len(questions)} questions and {len(answers)} answers\n")

    errors = []
    warnings = []

    fixes_made = 0

    # Check 1: For each answer, verify its linked questions have the answer back-linked
    print("Checking: answer.questions -> question.answers...")
    for aid, answer in answers.items():
        answer_text = answer.get('text', '')[:50]
        linked_questions = answer.get('questions', [])

        for qid in linked_questions:
            if qid not in questions:
                errors.append(f"Answer [{aid}] references non-existent question [{qid}]")
                continue

            question = questions[qid]
            question_answers = question.get('answers', [])

            if aid not in question_answers:
                errors.append(
                    f"Answer [{aid}] lists question [{qid}] but question doesn't list answer back\n"
                    f"  Answer: {answer_text}...\n"
                    f"  Question: {question.get('text', '')}"
                )
                if fix_mode:
                    if 'answers' not in question:
                        question['answers'] = []
                    question['answers'].append(aid)
                    fixes_made += 1
                    print(f"  FIXED: Added answer [{aid}] to question [{qid}].answers")

    # Check 2: For each question, verify its linked answers have the question back-linked
    print("Checking: question.answers -> answer.questions...")
    for qid, question in questions.items():
        question_text = question.get('text', '')
        linked_answers = question.get('answers', [])

        for aid in linked_answers:
            if aid not in answers:
                errors.append(f"Question [{qid}] references non-existent answer [{aid}]")
                continue

            answer = answers[aid]
            answer_questions = answer.get('questions', [])

            if qid not in answer_questions:
                errors.append(
                    f"Question [{qid}] lists answer [{aid}] but answer doesn't list question back\n"
                    f"  Question: {question_text}\n"
                    f"  Answer: {answer.get('text', '')[:50]}..."
                )
                if fix_mode:
                    if 'questions' not in answer:
                        answer['questions'] = []
                    answer['questions'].append(qid)
                    fixes_made += 1
                    print(f"  FIXED: Added question [{qid}] to answer [{aid}].questions")

    # Check 3: Find orphan questions (no answers)
    print("Checking: orphan questions (no answers)...")
    for qid, question in questions.items():
        if not question.get('answers'):
            warnings.append(f"Question [{qid}] has no answers: {question.get('text', '')}")

    # Check 4: Find orphan answers (no questions)
    print("Checking: orphan answers (no questions)...")
    for aid, answer in answers.items():
        if not answer.get('questions'):
            warnings.append(f"Answer [{aid}] has no questions: {answer.get('text', '')[:50]}...")

    # Report results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for err in errors:
            print(f"  - {err}")
    else:
        print("\n✓ No bidirectional link errors found!")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warn in warnings[:20]:  # Limit display
            print(f"  - {warn}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more warnings")
    else:
        print("\n✓ No orphan entries found!")

    print(f"\nSummary:")
    print(f"  Total questions: {len(questions)}")
    print(f"  Total answers: {len(answers)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Fixes made: {fixes_made}")

    # Save if fixes were made
    if fix_mode and fixes_made > 0:
        print(f"\nSaving {fixes_made} fixes to {STORE_PATH}...")
        with open(STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✓ Saved!")

    return len(errors) == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
