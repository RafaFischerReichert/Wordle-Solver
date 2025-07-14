from collections import Counter
import pickle
import os
from functools import lru_cache

# Global variables for caching
_feedback_cache = {}
_precomputed_patterns = {}
_cache_dirty = False  # Track if cache was updated
_cache_file = 'feedback_patterns_cache.pkl'

# Read and Parse Word Lists
def read_word_list(file_path):
    with open(file_path, 'r') as file:
        words = [line.strip() for line in file if line.strip()]
    return words

# Load word lists only once at module level
allowed_guesses = read_word_list('allowed_wordle_guesses.txt')
possible_answers = read_word_list('possible_wordle_answers.txt')

# Optimized feedback function with caching
@lru_cache(maxsize=1000000)  # Cache up to 1M feedback calculations
def get_feedback(guess, answer):
    """Optimized feedback function with caching for repeated calculations."""
    feedback = ['0'] * 5
    answer_copy = list(answer)

    # First pass: Check for correct letters in correct positions
    for i in range(5):
        if guess[i] == answer[i]:
            feedback[i] = '2'
            answer_copy[i] = None

    # Second pass: Check for correct letters in wrong positions
    for i in range(5):
        if feedback[i] == '0' and guess[i] in answer_copy:
            feedback[i] = '1'
            # Use a more efficient way to find and remove the first occurrence
            for j in range(5):
                if answer_copy[j] == guess[i]:
                    answer_copy[j] = None
                    break

    return ''.join(feedback)

# Precompute all feedback patterns for faster lookup
def precompute_feedback_patterns():
    """Precompute all feedback patterns between possible answers and allowed guesses."""
    global _precomputed_patterns
    global _cache_file
    
    # Try to load from cache file
    if os.path.exists(_cache_file):
        try:
            with open(_cache_file, 'rb') as f:
                _precomputed_patterns = pickle.load(f)
            print("Loaded precomputed feedback patterns from cache.")
            return
        except:
            print("Cache file corrupted, recomputing...")
    
    print("Precomputing feedback patterns (this may take a moment)...")
    
    # Precompute patterns for all possible answer-guess combinations
    # Include both allowed_guesses and possible_answers as valid guesses
    all_valid_guesses = list(set(allowed_guesses + possible_answers))
    for answer in possible_answers:
        _precomputed_patterns[answer] = {}
        for guess in all_valid_guesses:
            _precomputed_patterns[answer][guess] = get_feedback(guess, answer)
    
    # Save to cache file
    try:
        with open(_cache_file, 'wb') as f:
            pickle.dump(_precomputed_patterns, f)
        print("Saved feedback patterns to cache.")
    except:
        print("Warning: Could not save cache file.")

# Optimized filter function using precomputed patterns
def filter_possible_answers(guesses, feedbacks):
    """Optimized filter using precomputed feedback patterns."""
    global _cache_dirty
    filtered_answers = possible_answers[:]
    
    for guess, feedback in zip(guesses, feedbacks):
        if _precomputed_patterns:
            # Use precomputed patterns if available, but add to cache if missing
            new_filtered = []
            for word in filtered_answers:
                if word not in _precomputed_patterns:
                    _precomputed_patterns[word] = {}
                if guess not in _precomputed_patterns[word]:
                    # Compute and add to cache
                    _precomputed_patterns[word][guess] = get_feedback(guess, word)
                    _cache_dirty = True
                if _precomputed_patterns[word][guess] == feedback:
                    new_filtered.append(word)
            filtered_answers = new_filtered
        else:
            # Fallback to original method
            filtered_answers = [
                word for word in filtered_answers 
                if get_feedback(guess, word) == feedback
            ]
    
    return filtered_answers

# Guess selection strategies
_first_guess_cache = None

# Try to load precomputed first guess cache
_first_guess_cache_file = 'first_guesses_cache.pkl'
if os.path.exists(_first_guess_cache_file):
    try:
        with open(_first_guess_cache_file, 'rb') as f:
            _first_guess_cache = pickle.load(f)
        print("Loaded precomputed first guess from cache.")
    except Exception as e:
        print(f"Warning: Could not load first guess cache: {e}")

def minimax_entropy(possible_answers, allowed_guesses):
    global _cache_dirty
    # Use precomputed first guess if available and this is the initial state
    if _first_guess_cache and len(possible_answers) == len(possible_answers) and set(possible_answers) == set(read_word_list('possible_wordle_answers.txt')):
        fg = _first_guess_cache.get('minimax_entropy')
        if fg and (fg in allowed_guesses or fg in possible_answers):
            return fg
    # If no possible answers remain, return a default guess
    if len(possible_answers) == 0:
        raise ValueError("No possible answers found")
    # If only one possible answer remains, guess it!
    if len(possible_answers) == 1:
        return possible_answers[0]
    # If 2 or fewer possible answers, only guess from possible_answers
    # Otherwise, use both allowed_guesses and possible_answers
    if len(possible_answers) <= 2:
        guess_pool = possible_answers
    else:
        # Combine both lists, removing duplicates
        guess_pool = list(set(allowed_guesses + possible_answers))
    best_score = float('inf')
    best_guesses = []
    for guess in guess_pool:
        # Map feedback pattern to count of possible answers
        pattern_counts = {}
        if _precomputed_patterns:
            # Use precomputed patterns for much faster lookup, but handle missing entries
            for answer in possible_answers:
                if answer not in _precomputed_patterns:
                    _precomputed_patterns[answer] = {}
                if guess not in _precomputed_patterns[answer]:
                    _precomputed_patterns[answer][guess] = get_feedback(guess, answer)
                    _cache_dirty = True
                pattern = _precomputed_patterns[answer][guess]
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        else:
            # Fallback to original method
            for answer in possible_answers:
                pattern = get_feedback(guess, answer)
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        # Calculate expected size (entropy)
        total = sum(pattern_counts.values())
        expected = sum((count/total) * count for count in pattern_counts.values())
        if expected < best_score:
            best_score = expected
            best_guesses = [guess]
        elif expected == best_score:
            best_guesses.append(guess)
    # If no best guesses found, return first allowed guess
    if not best_guesses:
        return allowed_guesses[0]
    # Prefer a guess that is in possible_answers
    for guess in best_guesses:
        if guess in possible_answers:
            return guess
    # Otherwise, return any of the best guesses
    return best_guesses[0]

# Interactive game loop
def play_wordle(strategy_func, answer=None):
    """
    Play a game of Wordle.
    - strategy_func: function to select the next guess (e.g., letter_freq_heuristic or minimax_entropy)
    - answer: if provided, the game is simulated (auto-feedback); if None, user provides feedback
    """
    global _cache_dirty, _cache_file, _precomputed_patterns
    while True:
        guesses = []
        feedbacks = []
        possible = possible_answers[:]  # Start with all possible answers

        for attempt in range(1, 7):  # Wordle allows up to 6 guesses
            # Select guess
            guess = strategy_func(possible, allowed_guesses)
            print(f"Attempt {attempt}: {guess}")
            guesses.append(guess)

            # If only one possible answer remains, feedback is always 22222
            if len(possible) == 1:
                fb = "22222"
                print(f"Feedback: {fb}")
            else:
                # Get feedback
                if answer:
                    fb = get_feedback(guess, answer)
                    print(f"Feedback: {fb}")
                else:
                    fb = input("Enter feedback (e.g., 20100 or 'quit' to exit): ").strip()
                    if fb.lower() in ['quit', 'exit']:
                        print("Exiting game loop by user request.")
                        return
            feedbacks.append(fb)

            # Debug: print possible answers after feedback
            possible = filter_possible_answers(guesses, feedbacks)
            print(f"{len(possible)} possible answers remain.")
            if len(possible) <= 10:  # Only show all if 10 or fewer
                print(f"Possible answers: {possible}")
            else:
                print(f"First 5 possible answers: {possible[:5]}...")

            # Check for win
            if fb == "22222":
                print(f"Solved in {attempt} guesses! The answer was {guess}.")
                print ("Initiating next game... \n\n")
                break

        else:
            print("Failed to solve the puzzle.")

        # At the end of each game, persist the cache if dirty
        if _cache_dirty:
            try:
                with open(_cache_file, 'wb') as f:
                    pickle.dump(_precomputed_patterns, f)
                print("[Cache] Updated feedback patterns cache written to disk.")
                _cache_dirty = False
            except Exception as e:
                print(f"[Cache] Failed to write updated cache: {e}")

# GREEN = 2, YELLOW = 1, GRAY = 0
if __name__ == "__main__":
    # Precompute feedback patterns for faster execution
    precompute_feedback_patterns()
    play_wordle(minimax_entropy)