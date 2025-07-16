"""
Optimization script to precompute the optimal first guess for Wordle hard mode.
Run this script once to create the hard mode first guess cache file.
WARNING: This version checks ALL valid guesses and may take a long time to run.
"""

import pickle
from solver_hard_mode import minimax_entropy_hard_mode, allowed_guesses, possible_answers, enforce_hard_mode_constraints, get_feedback

def compute_best_first_guess_hard_mode():
    print("Computing best first guess for hard mode (minimax entropy) [FULL SEARCH]...")
    best_score = float('inf')
    best_guess = None
    guess_subset = list(set(allowed_guesses + possible_answers))  # Use ALL guesses
    for i, guess in enumerate(guess_subset):
        pattern_counts = {}
        for answer in possible_answers:
            fb = get_feedback(guess, answer)
            pattern_counts[fb] = pattern_counts.get(fb, 0) + 1
        total = sum(pattern_counts.values())
        expected = sum((count/total) * count for count in pattern_counts.values())
        if expected < best_score:
            best_score = expected
            best_guess = guess
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(guess_subset)}")
    print(f"Best first guess for hard mode minimax entropy: {best_guess} (expected remaining: {best_score:.1f})")
    with open('first_guesses_cache_hard_mode.pkl', 'wb') as f:
        pickle.dump({'minimax_entropy_hard_mode': best_guess}, f)
    print("✓ Saved hard mode first guess cache")

if __name__ == "__main__":
    compute_best_first_guess_hard_mode() 