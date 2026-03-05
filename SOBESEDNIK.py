import logging
import os
from litellm import acompletion
from DB import save_message, get_recent_messages

logging.basicConfig(level=logging.INFO)

# === ВСТАВЬ СВОЙ КЛЮЧ СЮДА ===
os.environ["GROQ_API_KEY"] = "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"

SYSTEM_PROMPT = """[BRITISH_FOOTBALL_MATE]
Ты — 18-летний британский парень из Манчестера, фанат United. Говоришь ТОЛЬКО на английском с сленгом. Тема — ТОЛЬКО ФУТБОЛ. Используй "proper worldie", "he's on fire", "nutmegged him", "bloody hell", "mate", "innit"."""

async def get_companion_response(user_id: int, user_text: str) -> str:
    history = await get_recent_messages(user_id, limit=10)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_text})

    await save_message(user_id, "user", user_text)

    try:
        response = await acompletion(
            model="groq/llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.8
        )
        answer = response.choices[0].message.content
        await save_message(user_id, "assistant", answer)
        return answer
    except Exception as e:
        logging.error(f"Groq error: {e}")
        return "Sorry mate, technical issue. Try again."