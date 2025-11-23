# duel_mode.py
import asyncio
from logic import check_guess, highlight_word
from llm_agent import llm_guess

async def bot_thinking(update):
    await update.message.reply_text("🤖 Bot myśli…")
    await asyncio.sleep(0.7)

async def duel_turn(update, game):
    await bot_thinking(update)

    word = llm_guess(game)
    feedback = check_guess(game["word"], word)

    game["bot_memory"].append((word, feedback))
    game["attempts_bot"] += 1

    await update.message.reply_text(
        f"🤖 {highlight_word(word, feedback)}"
    )

    return word == game["word"]






