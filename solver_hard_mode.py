import sys
from solver import (
    allowed_guesses, possible_answers, get_feedback, filter_possible_answers, minimax_entropy, precompute_feedback_patterns
)

def enforce_hard_mode_constraints(guesses, feedbacks, guess):
    """
    Returns True if the guess is valid under hard mode constraints given the history of guesses and feedbacks.
    - Green: must be present in the same position in every guess after found.
    - Yellow: must be present somewhere (not in the same position) in every guess after found.
    """
    green_positions = [None] * 5  # letter or None
    yellow_letters = set()
    yellow_positions = {}  # letter -> set of forbidden positions
    for prev_guess, fb in zip(guesses, feedbacks):
        for i, (g_letter, f) in enumerate(zip(prev_guess, fb)):
            if f == '2':
                green_positions[i] = g_letter
            elif f == '1':
                yellow_letters.add(g_letter)
                yellow_positions.setdefault(g_letter, set()).add(i)
    # Check green constraints
    for i, letter in enumerate(green_positions):
        if letter is not None and guess[i] != letter:
            return False
    # Check yellow constraints
    for letter in yellow_letters:
        if letter not in guess:
            return False
        for pos in yellow_positions[letter]:
            if guess[pos] == letter:
                return False
    return True

# The rest of the script will use this function to filter guesses in the strategy.

def minimax_entropy_hard_mode(possible, allowed, guesses, feedbacks):
    """
    Like minimax_entropy, but only considers guesses valid under hard mode constraints.
    """
    valid_allowed = [g for g in allowed if enforce_hard_mode_constraints(guesses, feedbacks, g)]
    valid_possible = [g for g in possible if enforce_hard_mode_constraints(guesses, feedbacks, g)]
    # If no valid guesses, fall back to all allowed
    if not valid_allowed:
        valid_allowed = allowed
    if not valid_possible:
        valid_possible = possible
    return minimax_entropy(valid_possible, valid_allowed)


def play_wordle_hard_mode(answer=None):
    """
    Play a game of Wordle in hard mode.
    - answer: if provided, the game is simulated (auto-feedback); if None, user provides feedback
    """
    precompute_feedback_patterns()
    guesses = []
    feedbacks = []
    possible = possible_answers[:]
    while True:
        guesses.clear()
        feedbacks.clear()
        possible = possible_answers[:]
        for attempt in range(1, 7):
            guess, score = minimax_entropy_hard_mode(possible, allowed_guesses, guesses, feedbacks)
            if score is not None:
                print(f"Attempt {attempt} (score: {score:.2f}): {guess}")
            else:
                print(f"Attempt {attempt} (score: N/A): {guess}")
            guesses.append(guess)
            if len(possible) == 1:
                fb = "22222"
                print(f"Feedback: {fb}")
            else:
                if answer:
                    fb = get_feedback(guess, answer)
                    print(f"Feedback: {fb}")
                else:
                    fb = input("Enter feedback (e.g., 20100 -- 2 for greens, 1 for yellows, 0 for grays/blacks) or 'quit' to exit): ").strip()
                    if fb.lower() in ['quit', 'exit']:
                        print("Exiting game loop by user request.")
                        return
            feedbacks.append(fb)
            possible = filter_possible_answers(guesses, feedbacks)
            print(f"{len(possible)} possible answers remain.")
            if len(possible) <= 10:
                print(f"Possible answers: {possible}")
            else:
                print(f"First 5 possible answers: {possible[:5]}...")
            if fb == "22222":
                print(f"Solved in {attempt} guesses! The answer was {guess}.")
                print ("Initiating next game... \n\n")
                break
        else:
            print("Failed to solve the puzzle.")
        # No 'Play again?' prompt; just start a new game unless user entered 'quit' or 'exit' above

if __name__ == "__main__":
    print("Wordle Hard Mode Solver\n======================\n")
    play_wordle_hard_mode()
