import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 1. Fetch lightweight news feed
feed_url = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1"
articles = []
try:
    req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req, timeout=10)
    root = ET.fromstring(response.read())
    for item in root.findall('.//item')[:3]:
        title = item.find('title')
        desc = item.find('description')
        if title is not None and title.text:
            articles.append({
                "title": title.text,
                "description": desc.text[:150] if desc is not None and desc.text else ""
            })
except Exception as e:
    print(f"Feed fetch error: {e}")

if not articles:
    articles = [{"title": "National Governance and Policy Updates", "description": "Key structural developments."}]

prompt = f"""
Act as an expert Indian Competitive Exam Faculty. Analyze these news items and create 3 high-yield exam study items.
Translate into English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the schema.

News: {json.dumps(articles, indent=2)}

Format per item:
- "Date": "{datetime.now().strftime('%Y-%m-%d')}"
- "Subject": "Current Affairs"
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

# 2. Resilient Multi-Model Fallback Sequence
fallback_models = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

final_response = None
for model_name in fallback_models:
    try:
        print(f"Attempting model: {model_name}...")
        final_response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"response_mime_type": "application/json", "response_schema": response_schema, "temperature": 0.3}
        )
        print(f"Successfully generated content using: {model_name}")
        break
    except Exception as e:
        print(f"Model {model_name} quota/rate limit reached or unavailable: {e}")
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
    print("Daily news updated successfully!")
else:
    print("Note: Temporary quota limits reached across available models. Exiting cleanly.")
    exit(0)
