import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Reliable feeds with proper browser User-Agent headers
feeds = [
    ("https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1", "National PIB"),
    ("https://www.thehindu.com/news/national/feeder/default.rss", "The Hindu National"),
    ("https://indianexpress.com/section/india/feed/", "Indian Express")
]

articles = []
for url, source_name in feeds:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        response = urllib.request.urlopen(req, timeout=10)
        root = ET.fromstring(response.read())
        for item in root.findall('.//item')[:4]:
            title_elem = item.find('title')
            desc_elem = item.find('description')
            if title_elem is not None and title_elem.text:
                articles.append({
                    "source": source_name,
                    "title": title_elem.text,
                    "description": desc_elem.text if desc_elem is not None and desc_elem.text else ""
                })
    except Exception as e:
        print(f"Skipping feed {source_name} due to error: {e}")

# Fallback static articles if feeds are temporarily blocked
if not articles:
    articles = [
        {"source": "Fallback", "title": "India's Economic Growth and Policy Updates", "description": "Key structural reforms and fiscal developments across sectors."},
        {"source": "Fallback", "title": "International Treaties and Global Summits", "description": "Major diplomatic developments affecting international relations."}
    ]

prompt = f"""
Act as an expert Indian Competitive Exam Faculty (UPSC, SSC CGL).
Analyze these news articles and convert them into high-yield exam study material.
Generate content in English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array of 10 items matching the schema.

News Articles: {json.dumps(articles[:10], indent=2)}

Format required per item:
- "Date": "{datetime.now().strftime('%Y-%m-%d')}"
- "Subject": "Polity / Economy / International Relations / Science"
- "Headline": {{"en": "...", "hi": "...", "bn": "..."}}
- "Summary": {{"en": "• Bullet 1 • Bullet 2", "hi": "• बिंदु 1 • बिंदु 2", "bn": "• পয়েন্ট ১ • পয়েন্ট ২"}}
- "Question": {{"en": "...", "hi": "...", "bn": "..."}}
- "Options": {{"en": "A) Opt1 | B) Opt2 | C) Opt3 | D) Opt4", "hi": "...", "bn": "..."}}
- "Explanation": {{"en": "Correct: B. Detailed explanation", "hi": "...", "bn": "..."}}
- "Source_Link": "https://pib.gov.in"
"""

lang_obj = {"type": "object", "properties": {"en": {"type": "string"}, "hi": {"type": "string"}, "bn": {"type": "string"}}, "required": ["en", "hi", "bn"]}
response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "Date": {"type": "string"},
            "Subject": {"type": "string"},
            "Headline": lang_obj,
            "Summary": lang_obj,
            "Question": lang_obj,
            "Options": lang_obj,
            "Explanation": lang_obj,
            "Source_Link": {"type": "string"}
        },
        "required": ["Date", "Subject", "Headline", "Summary", "Question", "Options", "Explanation"]
    }
}

final_response = None
for model_name in ["gemini-1.5-flash", "gemini-2.0-flash-lite"]:
    try:
        final_response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"response_mime_type": "application/json", "response_schema": response_schema, "temperature": 0.3}
        )
        break
    except Exception as e:
        print(f"Model {model_name} failed: {e}")
        continue

if final_response:
    new_data = json.loads(final_response.text)
    existing_data = []
    if os.path.exists('latest_news.json'):
        with open('latest_news.json', 'r') as f:
            try: existing_data = json.load(f)
            except: pass
    
    combined = new_data + existing_data
    with open('latest_news.json', 'w') as f:
        json.dump(combined[:150], f, indent=2)
    print("Daily news successfully generated and saved!")
else:
    print("Critical error: Failed to generate content from Gemini API.")
    exit(1)
