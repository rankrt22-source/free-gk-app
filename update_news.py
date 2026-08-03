import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from google import genai
from google.genai import types

# 1. Initialize the new Google Gen AI Client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. Fetch Live Updates from Official PIB RSS Feed
PIB_RSS_URL = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1"
try:
    req = urllib.request.Request(PIB_RSS_URL, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    rss_data = response.read()
except Exception as e:
    print(f"Error fetching RSS: {e}")
    exit(1)

# 3. Parse the XML Feed
root = ET.fromstring(rss_data)
latest_articles = []
for item in root.findall('./channel/item')[:5]:
    latest_articles.append({
        "title": item.find('title').text if item.find('title') is not None else "",
        "description": item.find('description').text if item.find('description') is not None else ""
    })

# 4. Formulate Prompt for Gemini
prompt = f"""
Act as an expert Indian Competitive Exam Faculty (UPSC, SSC CGL).
Analyze these news articles and convert them into structured exam study material.
Strictly output a JSON array.

News Articles: {json.dumps(latest_articles, indent=2)}

Format required:
[
  {{
    "Date": "{datetime.now().strftime('%Y-%m-%d')}",
    "Subject": "Polity/Economy/Science/Current Affairs",
    "Headline": "Concise summary of the news",
    "Summary": "• Bullet 1 • Bullet 2 • Bullet 3",
    "Question": "1 high-yield MCQ related to the news",
    "Options": "A) Option1 | B) Option2 | C) Option3 | D) Option4",
    "Explanation": "Detailed explanation of the correct answer",
    "Source_Link": "Exact URL"
  }}
]
"""

# 5. Define the Response Schema for Strict JSON Output
response_schema = types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "Date": types.Schema(type=types.Type.STRING),
            "Subject": types.Schema(type=types.Type.STRING),
            "Headline": types.Schema(type=types.Type.STRING),
            "Summary": types.Schema(type=types.Type.STRING),
            "Question": types.Schema(type=types.Type.STRING),
            "Options": types.Schema(type=types.Type.STRING),
            "Explanation": types.Schema(type=types.Type.STRING),
            "Source_Link": types.Schema(type=types.Type.STRING),
        },
        required=["Date", "Subject", "Headline", "Summary", "Question", "Options", "Explanation"]
    )
)

# 6. Generate JSON Output using the new SDK standard
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.2 
        ),
    )
    
    # 7. Save output to a file for the web app to read
    new_data = json.loads(response.text)
    
    existing_data = []
    if os.path.exists('latest_news.json'):
        with open('latest_news.json', 'r') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                pass
                
    combined_data = new_data + existing_data
    combined_data = combined_data[:100] # Keep the last 100 entries

    with open('latest_news.json', 'w') as f:
        json.dump(combined_data, f, indent=2)

    print("Daily content generated and saved successfully!")
except Exception as e:
    print(f"Error calling Gemini API: {e}")
