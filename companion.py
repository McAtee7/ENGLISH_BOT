import logging
import os
from litellm import acompletion
from DB import save_message, get_recent_messages, get_user_state, set_user_mode
from system_prompt import system_prompt_sobesednik, system_prompt_coach

logging.basicConfig(level=logging.INFO)

ROLE_PROMPTS = {
    "teammate": system_prompt_sobesednik,
    "coach": system_prompt_coach
}

async def get_companion_response(user_id: int, user_text: str) -> str:
    state = await get_user_state(user_id)
    role = state.get("role", "teammate")
    history = await get_recent_messages(user_id, 10)

    messages = [{"role": "system", "content": ROLE_PROMPTS[role]}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_text})

    await save_message(user_id, "user", user_text)

    try:
        response = await acompletion(
            model="groq/llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.85
        )
        answer = response.choices[0].message.content
        await save_message(user_id, "assistant", answer)
        return answer
    except Exception as e:
        logging.error(f"Companion error: {e}")
        return "Sorry mate, technical issue. Try again."
