import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

REPORTS_DIR = "reports"
DATA_FILE = os.path.join(REPORTS_DIR, "data.json")

# === Создание папки и JSON-файла при первом запуске ===
os.makedirs(REPORTS_DIR, exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def fetch_trending_repos():
    """Получает топ-5 трендовых репозиториев GitHub."""
    url = "https://api.github.com/search/repositories?q=stars:>10000&sort=stars&order=desc&per_page=5"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    data = response.json()

    if "items" not in data:
        print("⚠️ Ошибка: не удалось получить репозитории. Ответ GitHub:")
        print(data)
        return []

    return data["items"]


def analyze_with_gemini(description):
    """Отправляет описание проекта в Gemini API для анализа."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": f"Анализ коммерциализации проекта: {description}"}]
        }]
    }
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    result = r.json()

    # Пытаемся извлечь текст ответа
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return f"⚠️ Ошибка при анализе: {result}"


def load_analyzed():
    """Загружает список уже проанализированных репозиториев из JSON."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_analyzed(data):
    """Сохраняет обновлённый список анализов в JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_pdf(repo_name, analysis_text):
    """Создаёт PDF-отчёт с анализом."""
    safe_name = repo_name.replace("/", "_")
    pdf_path = os.path.join(REPORTS_DIR, f"{safe_name}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 50, f"Анализ проекта: {repo_name}")
    text = c.beginText(50, height - 80)
    text.setFont("Helvetica", 10)
    for line in analysis_text.split("\n"):
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()


def main():
    analyzed = load_analyzed()
    repos = fetch_trending_repos()
    new_analyses = []

    for repo in repos:
        name = repo["full_name"]
        html_url = repo["html_url"]
        description = repo["description"] or "Без описания"

        # Проверяем, не анализировался ли уже
        if any(r["name"] == name for r in analyzed):
            print(f"⏩ Пропущен: {name} (уже проанализирован)")
            continue

        print(f"🔍 Анализирую: {name}")
        analysis = analyze_with_gemini(description)
        save_pdf(name, analysis)

        analyzed.append({
            "name": name,
            "url": html_url,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        new_analyses.append(name)

    save_analyzed(analyzed)

    if new_analyses:
        print(f"✅ Новые анализы сохранены: {', '.join(new_analyses)}")
    else:
        print("✅ Новых проектов не найдено — всё уже проанализировано.")


if __name__ == "__main__":
    main()
