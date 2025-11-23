# llm_agent.py
import os
import ast
from dotenv import load_dotenv
from groq import Groq
from logic import PATTERN
from candidate_filter import load_dictionary, filter_candidates

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"


def ask_groq(prompt: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system",
             "content": "Jesteś solverem Wordle. Zawsze analizujesz podpowiedzi i wybierasz najlepszy ruch z listy kandydatów. Nie generuj słów spoza listy."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=50
    )
    return resp.choices[0].message.content.strip()


def extract_word(w):
    if w and len(w) == 5 and PATTERN.match(w):
        return w
    return None


def build_constraints(history):
    green = ["?"] * 5
    included = set()
    forbidden = set()
    yellow_pos = [set() for _ in range(5)]

    for word, fb in history:
        for i, mark in enumerate(fb):
            letter = word[i]

            if mark == "🟩":
                green[i] = letter
                included.add(letter)

            elif mark == "🟨":
                included.add(letter)
                yellow_pos[i].add(letter)

            elif mark == "⬜":
                if letter not in included:
                    forbidden.add(letter)

    return green, included, forbidden, yellow_pos


# загружаем словарь
DICTIONARY = load_dictionary()


def llm_guess(game):
    """
    ГИБРИДНАЯ ЛОГИКА:

    1. Фильтр → создаёт корректный список кандидатов.
    2. Модель → выбирает лучшее слово из этого списка.
    """

    history = game["bot_memory"]

    # 1) Получаем ограничения
    green, included, forbidden, yellow_pos = build_constraints(history)

    # 2) Кандидаты по фильтру
    candidates = filter_candidates(DICTIONARY, green, included, forbidden, yellow_pos)

    # удаляем уже использованные
    used = {w for w, _ in history}
    candidates = [c for c in candidates if c not in used]

    if not candidates:
        return "error"

    # ---- покaзи KANDYDACI в консоли ----
    print("KANDYDACI:", candidates)

    # 3) Подаём модели историю + кандидатов
    history_lines = [f"{w} -> {''.join(fb)}" for w, fb in history]
    history_text = "\n".join(history_lines) if history_lines else "Brak prób."

    prompt = f"""
Gramy w Wordle po polsku.

Twoje poprzednie próby (słowo → podpowiedź):
{history_text}

Lista kandydatów (już zgodna z logiką Wordle):
{', '.join(candidates)}

Zasady:
🟩A = litera A jest na właściwym miejscu.
🟨A = litera A jest w słowie, ale NIE na prawidłowej pozycji.
⬜A = litery A nie ma w słowie.

Twoje zadanie:
1) Przeanalizować historię i wywnioskować ograniczenia Wordle.
2) Ocenić, które słowo z listy kandydatów:
   - ma najwięcej unikalnych liter,
   - eliminuje najwięcej możliwości,
   - jest najbardziej informacyjne.
3) Wybrać NAJLEPSZE słowo z listy kandydatów.

!!! Wybierz TYLKO słowo z listy kandydatów.
!!! Nie dodawaj komentarzy.

Zwróć jedynie jedno słowo 5-literowe.
"""
    print("KANDYDACI:", candidates)
    raw = ask_groq(prompt)
    guess = extract_word(raw)

    if guess in candidates:
        return guess

    # fallback — если модель дала странное
    return candidates[0]













