import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from google import genai

# 1. Initialize the Google Gen AI Client
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

# 5. Define the Response Schema as a standard dictionary
response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "Date": {"type": "string"},
            "Subject": {"type": "string"},
            "Headline": {"type": "string"},
            "Summary": {"type": "string"},
            "Question": {"type": "string"},
            "Options": {"type": "string"},
            "Explanation": {"type": "string"},
            "Source_Link": {"type": "string"}
        },
        "required": ["Date", "Subject", "Headline", "Summary", "Question", "Options", "Explanation"]
    }
}

# 6. Self-Healing Model Selection Engine
models_to_test = [
    "gemini-2.0-flash-lite", 
    "gemini-1.5-pro",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-pro"
]

final_response = None

for model_name in models_to_test:
    try:
        print(f"Attempting to use model: {model_name}...")
        final_response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
                "temperature": 0.2
            }
        )
        print(f"SUCCESS! Using {model_name}")
        break # Exit the loop immediately once a working model is found
    except Exception as e:
        print(f"Model {model_name} rejected by API: {e}")
        continue

# If every single model fails, stop the script
if final_response is None:
    print("CRITICAL ERROR: All models failed. Your API key might not have access to any free-tier models.")
    exit(1)

# 7. Save output to a file for the web app to read
try:
    new_data = json.loads(final_response.text)
    
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
    print(f"Error formatting or saving data: {e}")
