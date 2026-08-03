import os
import json
import time
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

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

fallback_models = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

def call_gemini_safely(prompt, schema, task_name):
    for model_name in fallback_models:
        try:
            print(f"Generating {task_name} using {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": schema, "temperature": 0.4}
            )
            if response and response.text:
                new_data = json.loads(response.text)
                
                # SAFETY FIX 1: Unwrap if AI puts array inside a dictionary
                if isinstance(new_data, dict):
                    for val in new_data.values():
                        if isinstance(val, list):
                            new_data = val
                            break
                
                # SAFETY FIX 2: Ensure it is absolutely a list
                if not isinstance(new_data, list):
                    new_data = [new_data] if new_data else []
                    
                print(f"Successfully generated {len(new_data)} items for {task_name}.")
                return new_data
        except Exception as e:
            print(f"Model {model_name} failed for {task_name}: {e}")
            continue
    return []

# 1. Load Existing Data safely
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

# 2. Massive PYQ Bulk Generation across all core subjects
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

print("Starting massive bulk PYQ generation...")
for subj in subjects_pyq:
    prompt = f"""
    Act as an expert Indian Competitive Exam Setter (UPSC, SSC CGL).
    Generate 5 high-yield Previous Year Style Questions (MCQs) specifically for the subject: {subj}.
    Translate all content into English (en), Hindi (hi), and Bengali (bn).
    Output strictly as a JSON array matching the schema.
    """
    items = call_gemini_safely(prompt, pyq_schema, f"PYQs - {subj}")
    if items:
        pyq_data.extend(items)
    
    # 2-second pause to prevent hitting API rate limits during bulk loop
    time.sleep(2) 

# 3. Massive Cheat Sheet Bulk Generation across all core topics
subjects_notes = [
    "Constitutional Articles & Schedules",
    "Important Governor-Generals & Viceroys",
    "River Systems & Mountain Passes",
    "Five-Year Plans & Economic Reforms",
    "National Parks & Ramsar Sites",
    "Physics/Chemistry Laws & Vitamins"
]

print("Starting massive bulk Cheat Sheet generation...")
for subj in subjects_notes:
    prompt = f"""
    Act as an expert Indian Competitive Exam Faculty.
    Generate 3 detailed '1-Minute Cheat Sheets' (rapid revision notes with bullet points) specifically for: {subj}.
    Translate all content into English (en), Hindi (hi), and Bengali (bn).
    Output strictly as a JSON array matching the schema.
    """
    items = call_gemini_safely(prompt, notes_schema, f"Notes - {subj}")
    if items:
        notes_data.extend(items)
        
    time.sleep(2)

# 4. Save to files (Cap at 400 deep items to keep the app fast)
pyq_data = pyq_data[:400]
notes_data = notes_data[:400]

with open('pyq_bank.json', 'w') as f:
    json.dump(pyq_data, f, indent=2)

with open('cheat_sheets.json', 'w') as f:
    json.dump(notes_data, f, indent=2)

print(f"Bulk generation fully complete! Total PYQs: {len(pyq_data)}, Total Cheat Sheets: {len(notes_data)}")
