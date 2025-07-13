from collections import Counter
import pickle
import os
from functools import lru_cache

# Global variables for caching
_precomputed_patterns = {}
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

# Load precomputed feedback patterns
def load_feedback_patterns():
    """Load precomputed feedback patterns for faster lookup."""
    global _precomputed_patterns
    
    if os.path.exists(_cache_file):
        try:
            with open(_cache_file, 'rb') as f:
                _precomputed_patterns = pickle.load(f)
            print("Loaded precomputed feedback patterns from cache.")
            return True
        except:
            print("Cache file corrupted or incompatible.")
    else:
        print("No cache file found. Some operations may be slower.")
    
    return False

# Filter possible answers based on guesses and feedback
def filter_possible_answers(guesses, feedbacks):
    """Filter possible answers based on guesses and feedback patterns."""
    filtered_answers = possible_answers[:]
    
    for guess, feedback in zip(guesses, feedbacks):
        if _precomputed_patterns:
            # Use precomputed patterns if available
            new_filtered = []
            for word in filtered_answers:
                if word in _precomputed_patterns and guess in _precomputed_patterns[word]:
                    if _precomputed_patterns[word][guess] == feedback:
                        new_filtered.append(word)
                else:
                    # Fallback to computing feedback
                    if get_feedback(guess, word) == feedback:
                        new_filtered.append(word)
            filtered_answers = new_filtered
        else:
            # Fallback to original method
            filtered_answers = [
                word for word in filtered_answers 
                if get_feedback(guess, word) == feedback
            ]
    
    return filtered_answers

def validate_feedback(feedback):
    """Validate that feedback is in correct format (5 digits, each 0, 1, or 2)."""
    if len(feedback) != 5:
        return False
    return all(c in '012' for c in feedback)

def validate_guess(guess):
    """Validate that guess is a valid 5-letter word."""
    if len(guess) != 5:
        return False
    # Check against both allowed guesses and possible answers
    return guess.lower() in allowed_guesses or guess.lower() in possible_answers

def display_possible_answers(possible_answers):
    """Display all possible answers in a formatted way."""
    if not possible_answers:
        print("❌ No possible answers found with the given constraints!")
        return
    
    print(f"\n✅ Found {len(possible_answers)} possible answer(s):")
    
    # Display all answers in columns of 5
    for i in range(0, len(possible_answers), 5):
        row = possible_answers[i:i+5]
        print("  " + "  ".join(f"{word.upper()}" for word in row))

def main():
    """Main interactive function for the Wordle helper."""
    print("🎯 Wordle Helper - Narrow down possible answers based on your guesses!")
    print("=" * 60)
    print("Feedback format: 0 = gray, 1 = yellow, 2 = green")
    print("Example: '20100' means 2nd letter green, 1st letter yellow, rest gray")
    print("=" * 60)
    
    # Load feedback patterns
    load_feedback_patterns()
    
    guesses = []
    feedbacks = []
    possible = possible_answers[:]  # Start with all possible answers
    
    print(f"\n📚 Starting with {len(possible)} possible answers")
    
    while True:
        print(f"\n{'='*40}")
        print(f"Round {len(guesses) + 1}")
        print(f"{'='*40}")
        
        # Get user's guess
        while True:
            guess = input("Enter your guess (5-letter word): ").strip().lower()
            if validate_guess(guess):
                break
            else:
                print("❌ Invalid guess! Please enter a valid 5-letter word.")
        
        # Get feedback
        while True:
            feedback = input("Enter feedback (5 digits, 0/1/2): ").strip()
            if validate_feedback(feedback):
                break
            else:
                print("❌ Invalid feedback! Please enter 5 digits (0, 1, or 2).")
        
        guesses.append(guess)
        feedbacks.append(feedback)
        
        # Filter possible answers
        possible = filter_possible_answers(guesses, feedbacks)
        
        # Display results
        print(f"\n🎯 Your guess: {guess.upper()}")
        print(f"📊 Feedback: {feedback}")
        print(f"📈 Remaining possible answers: {len(possible)}")
        
        display_possible_answers(possible)
        
        # Check if solved
        if feedback == "22222":
            print(f"\n🎉 Congratulations! You found the answer: {guess.upper()}")
            break
        
        if not possible:
            print("\n❌ No possible answers found! There might be an error in your feedback.")
            break
        
        # Ask if user wants to continue
        continue_playing = input("\nContinue with another guess? (y/n): ").strip().lower()
        if continue_playing not in ('y', 'yes'):
            break
    
    print("\n👋 Thanks for using Wordle Helper!")

if __name__ == "__main__":
    main()
