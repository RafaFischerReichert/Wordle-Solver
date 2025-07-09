"""
Optimization script to precompute expensive calculations and cache them for faster Wordle solver initialization.
Run this script once to create cache files, then the main script will load them automatically.
"""

import pickle
import os
from collections import Counter
from script import read_word_list, get_feedback

def create_optimization_cache():
    """Create cache files for faster Wordle solver initialization."""
    
    print("Loading word lists...")
    allowed_guesses = read_word_list('allowed_wordle_guesses.txt')
    possible_answers = read_word_list('possible_wordle_answers.txt')
    
    print(f"Loaded {len(allowed_guesses)} allowed guesses and {len(possible_answers)} possible answers.")
    
    # Cache 1: Precompute all feedback patterns
    print("\n1. Precomputing feedback patterns...")
    feedback_cache = {}
    
    total_combinations = len(possible_answers) * len(allowed_guesses)
    current = 0
    
    for answer in possible_answers:
        feedback_cache[answer] = {}
        for guess in allowed_guesses:
            feedback_cache[answer][guess] = get_feedback(guess, answer)
            current += 1
            if current % 10000 == 0:
                print(f"Progress: {current}/{total_combinations} ({current/total_combinations*100:.1f}%)")
    
    # Save feedback cache
    with open('feedback_patterns_cache.pkl', 'wb') as f:
        pickle.dump(feedback_cache, f)
    print("✓ Saved feedback patterns cache")
    
    # Cache 2: Precompute letter frequency data for common scenarios
    print("\n2. Precomputing letter frequency data...")
    letter_freq_cache = {}
    
    # Cache for different answer pool sizes
    for pool_size in [10, 50, 100, 500, 1000, len(possible_answers)]:
        if pool_size <= len(possible_answers):
            # Sample the first pool_size answers
            sample_answers = possible_answers[:pool_size]
            letter_counts = Counter()
            for word in sample_answers:
                letter_counts.update(set(word))
            letter_freq_cache[pool_size] = dict(letter_counts)
    
    with open('letter_freq_cache.pkl', 'wb') as f:
        pickle.dump(letter_freq_cache, f)
    print("✓ Saved letter frequency cache")
    
    # Cache 3: Precompute best first guesses for different strategies
    print("\n3. Precomputing best first guesses...")
    first_guesses = {}
    
    # For minimax entropy strategy
    print("  Computing best first guess for minimax entropy...")
    best_score = float('inf')
    best_guess = None
    
    # Only check a subset of guesses for speed (top 1000 most common words)
    guess_subset = allowed_guesses[:1000]
    
    for i, guess in enumerate(guess_subset):
        pattern_counts = {}
        for answer in possible_answers:
            pattern = feedback_cache[answer][guess]
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        total = sum(pattern_counts.values())
        expected = sum((count/total) * count for count in pattern_counts.values())
        
        if expected < best_score:
            best_score = expected
            best_guess = guess
        
        if i % 100 == 0:
            print(f"    Progress: {i}/{len(guess_subset)}")
    
    first_guesses['minimax_entropy'] = best_guess
    print(f"  Best first guess for minimax entropy: {best_guess} (expected remaining: {best_score:.1f})")
    
    # For letter frequency strategy
    print("  Computing best first guess for letter frequency...")
    letter_counts = Counter()
    for word in possible_answers:
        letter_counts.update(set(word))
    
    def score(word):
        return sum(letter_counts[c] for c in set(word))
    
    best_guess_freq = max(allowed_guesses[:1000], key=score)
    first_guesses['letter_freq'] = best_guess_freq
    print(f"  Best first guess for letter frequency: {best_guess_freq}")
    
    with open('first_guesses_cache.pkl', 'wb') as f:
        pickle.dump(first_guesses, f)
    print("✓ Saved first guesses cache")
    
    print("\n✓ All caches created successfully!")
    print("The main script will now load these caches automatically for much faster initialization.")

if __name__ == "__main__":
    create_optimization_cache() 