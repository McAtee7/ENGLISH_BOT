
import asyncio
import requests
from bs4 import BeautifulSoup
from litellm import acompletion
from DB import get_user_state, set_user_mode

last_headlines = []

def fetch_bbc_news():
    url = "https://www.bbc.com/sport/football"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a', class_='ssrcss-1xznhic-PromoLink')[:10]
        return [link.get_text(strip=True) for link in links if link.get_text(strip=True)]
    except:
        return ["Новости временно недоступны."]

async def get_football_news() -> str:
    headlines = fetch_bbc_news()
    global last_headlines
    if set(headlines[:5]) == set(last_headlines[:5]):
        return "Я уже выводил тебе свежие новости, mate. Новых пока нет — попробуй позже."
    last_headlines = headlines[:5]

    prompt = f"""Ты британский футбольный комментатор в пабе.
Возьми эти 5 заголовков и сделай 5 отдельных подробных новостей (минимум 100 слов каждая).
Живой разговорный язык, без ссылок, без BBC.
Формат:
Название новости
Текст (100+ слов)

Заголовки:
{chr(10).join(headlines[:5])}"""

    try:
        r = await acompletion(
            model="groq/llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return r.choices[0].message.content
    except:
        return "Новости не загрузились, mate. Попробуй позже."
