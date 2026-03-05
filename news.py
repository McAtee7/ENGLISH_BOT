import asyncio
import requests
from bs4 import BeautifulSoup
import os
from litellm import acompletion

os.environ["GROQ_API_KEY"] = "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"

def fetch_bbc_news(keyword: str = ""):
    url = "https://www.bbc.com/sport/football"
    if keyword:
        url = f"https://www.bbc.com/sport/football/search?q={keyword.replace(' ', '+')}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a', class_='ssrcss-1xznhic-PromoLink')[:10]
        return [{'title': link.get_text(strip=True), 'link': 'https://www.bbc.com' + link.get('href', '')} for link in links if link.get('href')]
    except:
        return []

async def get_football_news(keyword: str = "") -> str:
    news = fetch_bbc_news(keyword)
    if not news:
        return "Новости не загрузились."

    headlines = "\n".join([f"- {n['title']} ({n['link']})" for n in news])
    prompt = f"""Ключевое слово: {keyword or 'футбол'}
Вот заголовки с BBC. Сделай живой подробный обзор на английском как в пабе, вставляй ссылки."""

    r = await acompletion(model="groq/llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt + "\n\nNews:\n" + headlines}])
    return r.choices[0].message.content