import os
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_trending_repos():
    url = "https://api.github.com/search/repositories?q=stars:>10000&sort=stars&order=desc&per_page=5"
    response = requests.get(url)
    return response.json()["items"]

def analyze_with_gemini(description):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + GEMINI_API_KEY
    payload = {
        "contents": [{
            "parts": [{"text": f"Анализ коммерциализации проекта: {description}"}]
        }]
    }
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    return r.json()

def main():
    repos = fetch_trending_repos()
    print("=== ТОП 5 ПРОЕКТОВ ===")
    for repo in repos:
        print(f"Название: {repo['name']}")
        print(f"Описание: {repo['description']}")
        result = analyze_with_gemini(repo['description'] or 'Без описания')
        print(f"Анализ: {result}\n{'='*50}\n")

if __name__ == "__main__":
    main()
