import os
import json
import random
from google import genai

# 1. Initialize Client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# The Core Exam Subjects
subjects = [
    "Indian Polity (Articles, Amendments, Parliament)",
    "Modern Indian History (Freedom Struggle, INM)",
    "Indian Geography (Rivers, Mountains, Climate)",
    "Indian Economy (Five Year Plans, RBI, GDP)",
    "General Science (Physics, Chemistry, Biology)",
    "Environment & Ecology (National Parks, Treaties)"
]

# Pick 3 random subjects for this run so we don't overwhelm the API
selected_subjects = random.sample(subjects, 3)

# 2. Formulate Prompts
pyq_prompt = f"""
Act as an expert Indian Competitive Exam Faculty (UPSC, SSC CGL).
Create exactly 3 high-yield Previous Year Style Questions (MCQs), one for each of these subjects: {selected_subjects}.
Generate content in English (en), Hindi (hi), and Bengali (bn).
Output a JSON array.
"""

notes_prompt = f"""
Act as an expert Indian Competitive Exam Faculty.
Create exactly 3 "1-Minute Cheat Sheets" (quick revision notes), one for each of these subjects: {selected_subjects}.
Generate content in English (en), Hindi (hi), and Bengali (bn).
Output a JSON array.
"""

# 3. Schemas
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

# 4. Self-Healing Model Resolver
available_models = []
try:
    for m in client.models.list():
        clean_name = m.name.replace('models/', '')
        if 'gemini' in clean_name and 'embed' not in clean_name:
            available_models.append(clean_name)
except Exception:
    available_models = ["gemini-1.5-flash", "gemini-2.0-flash-lite"]

def generate_and_save(prompt, schema, filename):
    for model_name in available_models:
        try:
            print(f"Generating {filename} using {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": schema, "temperature": 0.4}
            )
            
            new_data = json.loads(response.text)
            
            existing_data = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    try:
                        existing_data = json.load(f)
                    except: pass
            
            # Combine and keep the latest 200 items so the app doesn't crash old phones
            combined_data = new_data + existing_data
            combined_data = combined_data[:200]
            
            with open(filename, 'w') as f:
                json.dump(combined_data, f, indent=2)
                
            print(f"Successfully updated {filename}!")
            return True
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue
    print(f"Failed to generate {filename}")
    return False

# 5. Execute
print(f"Selected subjects for today: {selected_subjects}")
generate_and_save(pyq_prompt, pyq_schema, 'pyq_bank.json')
generate_and_save(notes_prompt, notes_schema, 'cheat_sheets.json')
