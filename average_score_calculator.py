from solver import minimax_entropy, read_word_list
from concurrent.futures import ProcessPoolExecutor, as_completed

# Load word lists only once at module level
allowed_guesses = read_word_list('allowed_wordle_guesses.txt')
possible_answers = read_word_list('possible_wordle_answers.txt')


def simulate_game(answer, strategy_func, allowed_guesses, possible_answers):
    guesses = []
    feedbacks = []
    possible = possible_answers[:]
    for attempt in range(1, 7):
        guess, _ = strategy_func(possible, allowed_guesses)
        guesses.append(guess)
        if guess == answer:
            return attempt
        fb = minimax_entropy.get_feedback(guess, answer) if hasattr(minimax_entropy, 'get_feedback') else None
        if not fb:
            # fallback to global get_feedback
            from solver import get_feedback
            fb = get_feedback(guess, answer)
        feedbacks.append(fb)
        possible = [word for word in possible if get_feedback(guess, word) == fb]
    return 7  # If not solved in 6 tries, return 7 as a fail-safe


def calculate_average_tries():
    total_tries = 0
    results = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(simulate_game, answer, minimax_entropy, allowed_guesses, possible_answers): answer for answer in possible_answers}
        for idx, future in enumerate(as_completed(futures)):
            tries = future.result()
            results.append(tries)
            if (idx + 1) % 100 == 0:
                print(f"Simulated {idx + 1} games...")
    average = sum(results) / len(results)
    print(f"Average number of tries: {average:.4f}")
    # Also write the average to a file
    with open("average_tries.txt", "w") as f:
        f.write(f"{average:.4f}\n")


if __name__ == "__main__":
    calculate_average_tries()

