# solo_mode.py
from logic import check_guess

def solo_turn(game, text):
    feedback = check_guess(game["word"], text)
    game["user_history"].append((text, feedback))
    game["attempts_user"] += 1

    user_won = (text == game["word"])
    user_lost = (game["attempts_user"] >= 6 and not user_won)

    return feedback, user_won, user_lost


