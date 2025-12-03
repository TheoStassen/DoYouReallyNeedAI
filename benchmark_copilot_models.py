#!/usr/bin/env python3
"""Benchmark copilot query latency for different model choices and reuse patterns.

Usage: python scripts/benchmark_copilot_models.py

Outputs times for cold start (reset=True) and warm calls (reset=False).
"""
import time
from copilot_use import copilot_query

PROMPT = (
    "En français, donne UNIQUEMENT un résumé en AU PLUS 3 mots, puis '||', puis l'id entier de la question la plus proche. "
    "Réponds SUR UNE SEULE LIGNE, sans ponctuation ni guillemets, rien d'autre. Exemple: joli logo rapide||74\n"
    "Question: 'creation d'un joli logo'"
)

MODELS = [
    None,  # default
]


def measure(model, reset, runs=3):
    times = []
    for i in range(runs):
        start = time.time()
        _ = copilot_query(PROMPT, reset=reset, model=model)
        times.append(time.time() - start)
    return times


def main():
    for m in MODELS:
        name = m or "<default>"
        print(f"Model: {name}")
        # cold: reset=True
        # cold = measure(m, reset=True, runs=2)
        # print("  Cold calls:", [round(t, 2) for t in cold])
        # warm: reset=False
        warm = measure(m, reset=False, runs=2)
        print("  Warm calls:", [round(t, 2) for t in warm])
        print()

if __name__ == '__main__':
    main()

