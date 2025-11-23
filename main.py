# main.py
import os
import random
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

from logic import valid_word, highlight_word
from solo_mode import solo_turn
from duel_model import duel_turn

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# słowa 5-literowe
with open("rzeczowniki.txt", "r", encoding="utf-8") as f:
    NOUNS = {w.strip().lower() for w in f if len(w.strip()) == 5}

games = {}


# ---------------------------------------------------------
# MENUS
# ---------------------------------------------------------
def start_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎮 Gra solo", callback_data="solo"),
            InlineKeyboardButton("🤖 Gra z botem", callback_data="duel"),
        ],
        [InlineKeyboardButton("❓ Pomoc", callback_data="pomoc")]
    ])


def ingame_menu():   # ❗ без "pomoc"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Nowa gra", callback_data="nowa")]
    ])


def end_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Nowa gra (ten sam tryb)", callback_data="again")],
        [InlineKeyboardButton("🔙 Wróć do wyboru trybu", callback_data="back")]
    ])


# ---------------------------------------------------------
# START
# ---------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👋 Wybierz tryb gry:"
    markup = start_menu()

    if update.message:
        await update.message.reply_text(text, reply_markup=markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=markup)


# ---------------------------------------------------------
# HELP
# ---------------------------------------------------------
async def help_message(update: Update):
    text = (
        "❓ *Zasady SŁOWOKU*\n\n"
        "🟩 Litera na właściwym miejscu\n"
        "🟨 Litera jest w słowie, ale w złym miejscu\n"
        "⬜ Litery nie ma w słowie\n\n"
        "🎮 SOLO — zgadujesz\n"
        "🤖 DUEL — grasz przeciwko botowi\n"
    )

    await update.callback_query.edit_message_text(
        text, parse_mode="Markdown", reply_markup=start_menu()
    )


# ---------------------------------------------------------
# CREATE GAME
# ---------------------------------------------------------
def create_game(uid: int, mode: str):
    word = random.choice(list(NOUNS))
    games[uid] = {
        "mode": mode,
        "word": word,
        "attempts_user": 0,
        "attempts_bot": 0,
        "finished": False,
        "bot_memory": [],
        "user_history": []
    }


async def choose_mode(update: Update, mode: str):
    q = update.callback_query
    uid = q.from_user.id

    create_game(uid, mode)

    if mode == "solo":
        await q.edit_message_text("🎮 Tryb SOLO — zgaduj słowo!")
    else:
        await q.edit_message_text("🤖 Tryb DUEL — zaczynaj pierwszy!")

async def pomoc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    in_game = uid in games and not games[uid]["finished"]

    text = (
        "❓ *Zasady SŁOWOKU*\n\n"
        "🟩 Litera na właściwym miejscu\n"
        "🟨 Litera jest w słowie, ale w złym miejscu\n"
        "⬜ Litery nie ma w słowie\n\n"
        "🎮 SOLO — zgadujesz\n"
        "🤖 DUEL — grasz przeciwko botowi\n"
    )

    if in_game:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=ingame_menu())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=start_menu())

async def nowa_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # Nie ma gry — pokaż start
    if uid not in games:
        return await start(update, context)

    # Gra istnieje — restart trybu
    mode = games[uid]["mode"]
    create_game(uid, mode)

    await update.message.reply_text(
        f"🔄 Nowa gra ({mode.upper()}) — zaczynamy!",
        reply_markup=ingame_menu()
    )

# ---------------------------------------------------------
# BUTTON HANDLER
# ---------------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    uid = q.from_user.id

    # Start menu
    if data == "solo":
        return await choose_mode(update, "solo")

    if data == "duel":
        return await choose_mode(update, "duel")

    # Help
    if data == "pomoc":
        return await help_message(update)

    # Nowa gra – działa TYLKO w grze
    if data == "nowa":
        if uid not in games:
            return await start(update, context)

        mode = games[uid]["mode"]
        create_game(uid, mode)

        return await q.edit_message_text(
            f"🔄 Nowa gra ({mode.upper()}) — zaczynamy!",
        )

    # Nowa po zakończeniu gry
    if data == "again":
        mode = games[uid]["mode"]
        create_game(uid, mode)
        return await q.edit_message_text(
            f"🔁 Nowa gra ({mode.upper()}) — powodzenia!"
        )

    if data == "back":
        return await start(update, context)


# ---------------------------------------------------------
# WORD GUESS HANDLER
# ---------------------------------------------------------
async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in games:
        return await update.message.reply_text("Wpisz /start")

    g = games[uid]

    if g["finished"]:
        return await update.message.reply_text("Gra zakończona — wpisz /start.")

    text = update.message.text.strip().lower()

    if not valid_word(text):
        return await update.message.reply_text("⚠️ Wpisz polskie słowo 5-literowe.")

    # -----------------------------------------
    # 1️⃣ USER TURN — анализируем ход игрока
    # -----------------------------------------
    fb, win, lose = solo_turn(g, text)
    colored = highlight_word(text, fb)

    # 🏆 пользователь выиграл
    if win:
        g["finished"] = True
        return await update.message.reply_text(
            f"{colored}\n\n🏆 Wygrałeś!\nHasło: {g['word'].upper()}\n\nCo chcesz zrobić?",
            reply_markup=end_menu()
        )

    # 💀 пользователь проиграл в SOLO
    if g["mode"] == "solo" and lose:
        g["finished"] = True
        return await update.message.reply_text(
            f"{colored}\n\n💀 Przegrałeś!\nHasło: {g['word'].upper()}\n\nCo chcesz zrobić?",
            reply_markup=end_menu()
        )

    # -----------------------------------------
    # 2️⃣ настало время показать ХОД ИГРОКА
    # (в режиме DUEL бот ещё НЕ ходит)
    # -----------------------------------------
    if g["mode"] == "duel":

        # Сообщение игроку (его результат + меню)
        await update.message.reply_text(
            f"{colored}\n\n📊 Twoja próba {g['attempts_user']}/6 — co dalej?",
            reply_markup=ingame_menu()  # только Nowa
        )

        # -------------------------------------
        # 3️⃣ BOT TURN (после анализа игрока)
        # -------------------------------------
        bot_won = await duel_turn(update, g)

        # 💀 бот выиграл
        if bot_won:
            g["finished"] = True
            return await update.message.reply_text(
                f"💀 Bot wygrał!\nHasło: {g['word'].upper()}\n\nCo chcesz zrobić?",
                reply_markup=end_menu()
            )

        # 🤝 ничья
        if g["attempts_user"] >= 6 and g["attempts_bot"] >= 6:
            g["finished"] = True
            return await update.message.reply_text(
                f"🤝 Remis!\nHasło: {g['word'].upper()}\n\nCo chcesz zrobić?",
                reply_markup=end_menu()
            )

        # ход продолжается
        return

    # -----------------------------------------
    # SOLO — продолжаем игру
    # -----------------------------------------
    await update.message.reply_text(
        f"{colored}\n\n📊 Próba {g['attempts_user']}/6 — co dalej?",
        reply_markup=ingame_menu()
    )




# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pomoc", pomoc_cmd))
    app.add_handler(CommandHandler("nowa", nowa_cmd))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))

    app.run_polling()


if __name__ == "__main__":
    main()





