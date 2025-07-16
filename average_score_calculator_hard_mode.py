from solver_hard_mode import minimax_entropy_hard_mode, enforce_hard_mode_constraints, get_feedback, allowed_guesses, possible_answers
from concurrent.futures import ProcessPoolExecutor, as_completed

def simulate_game_hard_mode(answer):
    guesses = []
    feedbacks = []
    possible = possible_answers[:]
    for attempt in range(1, 7):
        guess, _ = minimax_entropy_hard_mode(possible, allowed_guesses, guesses, feedbacks)
        guesses.append(guess)
        if guess == answer:
            return attempt
        fb = get_feedback(guess, answer)
        feedbacks.append(fb)
        possible = [word for word in possible if get_feedback(guess, word) == fb]
    return 7  # If not solved in 6 tries, return 7 as a fail-safe

def calculate_average_tries_hard_mode():
    total_tries = 0
    results = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(simulate_game_hard_mode, answer): answer for answer in possible_answers}
        for idx, future in enumerate(as_completed(futures)):
            tries = future.result()
            results.append(tries)
            if (idx + 1) % 100 == 0:
                print(f"Simulated {idx + 1} games...")
    average = sum(results) / len(results)
    print(f"[HARD MODE] Average number of tries: {average:.4f}")
    # Also write the average to a file
    with open("average_tries_hard_mode.txt", "w") as f:
        f.write(f"{average:.4f}\n")

if __name__ == "__main__":
    calculate_average_tries_hard_mode()
