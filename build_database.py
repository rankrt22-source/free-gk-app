import os
import json
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

fallback_models = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

lang_obj = {"type": "object", "properties": {"en": {"type": "string"}, "hi": {"type": "string"}, "bn": {"type": "string"}}, "required": ["en", "hi", "bn"]}

pyq_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "Exam": {"type": "string"},
            "Subject": {"type": "string"},
            "Question": lang_obj,
            "Options": lang_obj,
            "Explanation": lang_obj
        },
        "required": ["Exam", "Subject", "Question", "Options", "Explanation"]
    }
}

notes_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "Subject": {"type": "string"},
            "Time": {"type": "string"},
            "Title": lang_obj,
            "Content": lang_obj
        },
        "required": ["Subject", "Time", "Title", "Content"]
    }
}

def call_gemini(prompt, schema):
    for model_name in fallback_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": schema, "temperature": 0.4}
            )
            if response and response.text:
                return json.loads(response.text)
        except Exception as e:
            continue
    return []

# Load existing data to preserve what's already there
pyq_data = []
if os.path.exists('pyq_bank.json'):
    try:
        with open('pyq_bank.json', 'r') as f:
            pyq_data = json.load(f)
    except: pass

notes_data = []
if os.path.exists('cheat_sheets.json'):
    try:
        with open('cheat_sheets.json', 'r') as f:
            notes_data = json.load(f)
    except: pass

# 1. Exhaustive PYQ Subjects
subjects_pyq = [
    "Indian Art, Culture & Heritage",
    "Ancient & Medieval History",
    "Modern Indian History",
    "Indian Polity & Constitution",
    "Indian Economy & Budget",
    "Physical & Indian Geography",
    "General Science & Technology",
    "Environment & Ecology"
]

print("Starting single-run comprehensive multi-subject build...")

for subj in subjects_pyq:
    print(f"Fetching PYQs for: {subj}...")
    prompt = f"""
    Act as an expert Indian Competitive Exam Setter (UPSC, SSC CGL).
    Generate 5 high-yield Previous Year Style Questions (MCQs) specifically for the subject: {subj}.
    Translate all content into English (en), Hindi (hi), and Bengali (bn).
    Output strictly as a JSON array matching the schema.
    """
    items = call_gemini(prompt, pyq_schema)
    if items:
        pyq_data = items + pyq_data

# 2. Exhaustive Cheat Sheet Topics
subjects_notes = [
    "Constitutional Articles & Schedules",
    "Important Governor-Generals & Viceroys",
    "River Systems & Mountain Passes",
    "Five-Year Plans & Economic Reforms",
    "National Parks & Ramsar Sites",
    "Physics/Chemistry Laws & Vitamins"
]

for subj in subjects_notes:
    print(f"Fetching Cheat Sheets for: {subj}...")
    prompt = f"""
    Act as an expert Indian Competitive Exam Faculty.
    Generate 3 detailed '1-Minute Cheat Sheets' (rapid revision notes with bullet points) specifically for: {subj}.
    Translate all content into English (en), Hindi (hi), and Bengali (bn).
    Output strictly as a JSON array matching the schema.
    """
    items = call_gemini(prompt, notes_schema)
    if items:
        notes_data = items + notes_data

# Cap and save
pyq_data = pyq_data[:400]
notes_data = notes_data[:400]

with open('pyq_bank.json', 'w') as f:
    json.dump(pyq_data, f, indent=2)

with open('cheat_sheets.json', 'w') as f:
    json.dump(notes_data, f, indent=2)

print(f"Successfully completed! Total PYQs: {len(pyq_data)}, Total Cheat Sheets: {len(notes_data)}")
