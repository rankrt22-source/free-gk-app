import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Fetch fewer items to stay well within free-tier token limits
feeds = [
    ("https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1", "National PIB"),
    ("https://www.thehindu.com/news/national/feeder/default.rss", "The Hindu")
]

articles = []
for url, source_name in feeds:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10)
        root = ET.fromstring(response.read())
        for item in root.findall('.//item')[:2]: # Reduced to 2 items per feed to save tokens
            title = item.find('title')
            desc = item.find('description')
            if title is not None and title.text:
                articles.append({
                    "source": source_name,
                    "title": title.text,
                    "description": desc.text[:200] if desc is not None and desc.text else "" # Truncate description length
                })
    except Exception as e:
        print(f"Skipping feed {source_name}: {e}")

if not articles:
    articles = [{"source": "Fallback", "title": "National Policy and Governance Updates", "description": "Key structural reforms."}]

prompt = f"""
Act as an expert Indian Competitive Exam Faculty (UPSC, SSC CGL).
Analyze these news items and create 5 high-yield exam study items.
Translate into English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the schema.

News: {json.dumps(articles, indent=2)}

Format per item:
- "Date": "{datetime.now().strftime('%Y-%m-%d')}"
- "Subject": "Polity / Economy / Current Affairs"
- "Headline": {{"en": "...", "hi": "...", "bn": "..."}}
- "Summary": {{"en": "• Point 1", "hi": "• बिंदु 1", "bn": "• পয়েন্ট ১"}}
- "Question": {{"en": "...", "hi": "...", "bn": "..."}}
- "Options": {{"en": "A) Opt1 | B) Opt2 | C) Opt3 | D) Opt4", "hi": "...", "bn": "..."}}
- "Explanation": {{"en": "Correct: B. Explanation", "hi": "...", "bn": "..."}}
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
# Prioritize gemini-1.5-flash for stable free-tier limits
for model_name in ["gemini-1.5-flash", "gemini-2.0-flash"]:
    try:
        print(f"Attempting model: {model_name}")
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
        json.dump(combined[:100], f, indent=2)
    print("Success!")
else:
    print("Error: All models exhausted or failed.")
    exit(1)
