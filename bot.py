# -*- coding: utf-8 -*-
import os
import threading
from flask import Flask
import telebot
from exa_py import Exa
from tavily import TavilyClient
from datetime import datetime, timedelta

# Настройка веб-сервера для бесплатного Web Service на Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Baku News Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Ваши токены (укажите ваш токен от BotFather)
TELEGRAM_TOKEN = "9161073063:AAEqlqeBABRXJT-4M548DRYUq8qPDpygt4I"
EXA_API_KEY = "2822e236-d7d2-41ab-ad8f-ff551bf0bf39"
TAVILY_API_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
exa = Exa(api_key=EXA_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Бот мониторинга активен. Отправь /news для получения дайджеста за 24 часа.")

@bot.message_handler(commands=['news'])
def fetch_news(message):
    bot.send_message(message.chat.id, "🔍 Собираю свежие новости за последние 24 часа...")
    
    # Строго последние 24 часа
    start_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    search_queries = [
        {"lang": "🇬🇧 English", "query": "Azerbaijan geopolitics economy energy diplomacy Baku"},
        {"lang": "🇩🇪 German", "query": "Aserbaidschan Politik Wirtschaft Energie Baku"},
        {"lang": "🇫🇷 French", "query": "Azerbaïdjan économie politique énergie Bakou"},
        {"lang": "🇪🇸 Spanish", "query": "Azerbaiyán política economía energía Bakú"}
    ]
    
    report = "📰 *ОПЕРАТИВНЫЙ ДАЙДЖЕСТ (24 часа)*\n\n"
    report += "== *Глобальная аналитика (Exa AI)* ==\n\n"
    
    seen_urls = set()

    for item_q in search_queries:
        report += f"*{item_q['lang']}*\n"
        try:
            response = exa.search(
                query=item_q["query"],
                type="neural",
                category="news",
                start_published_date=start_date,
                num_results=3
            )
            
            count = 0
            for item in response.results:
                if item.url in seen_urls:
                    continue
                seen_urls.add(item.url)
                count += 1
                report += f"• [{item.title or 'Ссылка'}]({item.url})\n"
                if count >= 3:
                    break
            if count == 0:
                report += "— Нет новых публикаций\n"
            report += "\n"
        except Exception:
            report += "— Ошибка получения данных\n\n"

    report += "== *Оперативная лента (Tavily)* ==\n\n"
    try:
        tav_response = tavily.search(
            query="Azerbaijan geopolitics OR economy OR energy",
            search_depth="advanced",
            topic="news",
            days=1,
            max_results=5
        )
        t_results = tav_response.get("results", [])
        if t_results:
            for idx, item in enumerate(t_results[:5], 1):
                report += f"{idx}. [{item.get('title')}]({item.get('url')})\n"
        else:
            report += "— Нет оперативных новостей за 24 часа\n"
    except Exception:
        report += "— Ошибка получения данных Tavily\n"

    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == '__main__':
    # Запускаем веб-сервер в отдельном потоке для Render Web Service
    t = threading.Thread(target=run_web)
    t.start()
    
    # Запуск бота
    bot.infinity_polling()
