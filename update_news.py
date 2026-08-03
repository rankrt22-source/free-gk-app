import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from google import genai
from google.genai import types
from datetime import datetime

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

try:
    req = urllib.request.Request("https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1", headers={'User-Agent': 'Mozilla/5.0'})
    rss_data = urllib.request.urlopen(req).read()
    root = ET.fromstring(rss_data)
    
    articles = []
    for item in root.findall('./channel/item')[:5]:
        articles.append({
            "title": item.find('title').text if item.find('title') is not None else "",
            "description": item.find('description').text if item.find('description') is not None else ""
        })

    prompt = f"""
    Act as an expert Indian Competitive Exam Faculty (UPSC, SSC CGL).
    Analyze these news articles: {json.dumps(articles)}.
    Strictly output ONLY a JSON array with this format:
    [
      {{
        "Date": "{datetime.now().strftime('%Y-%m-%d')}",
        "Subject": "Polity/Economy/Science",
        "Headline": "Concise Headline",
        "Summary": "• Bullet 1 • Bullet 2 • Bullet 3",
        "Question": "1 high-yield MCQ",
        "Options": "A) | B) | C) | D)",
        "Explanation": "Detailed Answer Explanation",
        "Source_Link": "https://pib.gov.in"
      }}
    ]
    """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )

    with open('latest_news.json', 'w') as f:
        f.write(response.text)
    print("News update successfully generated!")

except Exception as e:
    print(f"Error updating news: {e}")
