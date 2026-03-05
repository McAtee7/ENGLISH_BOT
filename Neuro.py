import os
from litellm import acompletion

os.environ["GROQ_API_KEY"] = "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"

async def get_dictionary_response(word: str) -> str:
    base_prompt = f"Ты футбольный эксперт. Дай точный перевод и объяснение термина '{word}' на английском с примерами из матчей."

    answers = []
    for _ in range(3):  # три вызова = "несколько нейросетей"
        try:
            r = await acompletion(model="groq/llama-3.3-70b-versatile", messages=[{"role": "user", "content": base_prompt}])
            answers.append(r.choices[0].message.content)
        except:
            pass

    if not answers:
        return "Word not found, mate."

    final_prompt = f"""Вот 3 ответа про термин '{word}':
{chr(10).join([f'---\n{a}' for a in answers])}

Сделай среднее арифметическое: лучший вариант на английском с примерами."""

    final = await acompletion(model="groq/llama-3.3-70b-versatile", messages=[{"role": "user", "content": final_prompt}])
    return final.choices[0].message.content