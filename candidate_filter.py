# candidate_filter.py
from logic import PATTERN


def load_dictionary(path="rzeczowniki.txt"):
    words = []
    with open(path, "r", encoding="utf-8") as f:
        for w in f:
            w = w.strip().lower()
            if len(w) == 5 and PATTERN.match(w):
                words.append(w)
    return words


def filter_candidates(dictionary, green, included, forbidden, yellow_pos):
    """
    Фильтрует кандидатов по правилам Wordle.
    """
    result = []

    for word in dictionary:
        ok = True

        # 1. Зеленые позиции
        for i in range(5):
            if green[i] != "?" and word[i] != green[i]:
                ok = False
                break
        if not ok:
            continue

        # 2. Обязательные буквы
        if not included.issubset(set(word)):
            continue

        # 3. Запрещённые буквы
        if any(letter in word for letter in forbidden):
            continue

        # 4. Жёлтые позиции
        for i in range(5):
            if word[i] in yellow_pos[i]:
                ok = False
                break
        if not ok:
            continue

        result.append(word)

    return result

