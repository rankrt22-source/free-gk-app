import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Fetch from PIB (National) and a Global RSS feed simultaneously
PIB_RSS_URL = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1"
BBC_RSS_URL = "http://feeds.bbci.co.uk/news/world/rss.xml"

articles = []

def fetch_feed(url, source_tag):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        root = ET.fromstring(response.read())
        for item in root.findall('./channel/item')[:5]:
            articles.append({
                "source": source_tag,
                "title": item.find('title').text if item.find('title') is not None else "",
                "description": item.find('description').text if item.find('description') is not None else ""
            })
    except Exception as e:
        print(f"Error fetching {source_tag}: {e}")

fetch_feed(PIB_RSS_URL, "National (India)")
fetch_feed(BBC_RSS_URL, "Global / International")

if not articles:
    print("No articles fetched.")
    exit(1)

prompt = f"""
Act as an expert Indian Competitive Exam Faculty (UPSC, SSC CGL).
Analyze these National and Global news articles and convert them into high-yield exam study material. Ensure a balanced mix of Indian national updates and international/global current affairs.
Generate content in English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array of 10 items matching the schema.

News Articles: {json.dumps(articles, indent=2)}

Format required per item:
- "Date": "{datetime.now().strftime('%Y-%m-%d')}"
- "Subject": "National Affairs / International Relations / Economy / Science"
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

available_models = ["gemini-1.5-flash", "gemini-2.0-flash-lite"]
final_response = None
for model_name in available_models:
    try:
        final_response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"response_mime_type": "application/json", "response_schema": response_schema, "temperature": 0.3}
        )
        break
    except Exception as e:
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
    print("Daily global & national news updated successfully!")
