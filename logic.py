# logic.py
import re

# польский алфавит
POLISH_LETTERS = "aąbcćdeęfghijklłmnńoóprsśtuwyzźż"

# регулярка для проверки слова
PATTERN = re.compile(rf"^[{POLISH_LETTERS}]+$", re.IGNORECASE)


def check_guess(secret, guess):
    """
    Возвращает подсказки Wordle: 🟩🟨⬜
    """
    result = ["⬜"] * 5
    secret_chars = list(secret)

    # зелёные
    for i in range(5):
        if guess[i] == secret[i]:
            result[i] = "🟩"
            secret_chars[i] = None

    # жёлтые
    for i in range(5):
        if result[i] == "🟩":
            continue
        if guess[i] in secret_chars:
            result[i] = "🟨"
            secret_chars[secret_chars.index(guess[i])] = None

    return result


def highlight_word(guess, feedback):
    """
    Возвращает подсвеченное слово с цветными квадратами.
    """
    return "".join(f"{mark}\u200d{letter.upper()}" for letter, mark in zip(guess, feedback))


def valid_word(word):
    """
    Проверяет:
    - 5 букв
    - только польские буквы
    """
    return (
        len(word) == 5
        and PATTERN.match(word) is not None
    )


