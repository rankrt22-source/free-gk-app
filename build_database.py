import os
import json
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

pyq_prompt = """
Act as an expert Indian Competitive Exam Setter (UPSC, SSC CGL, State PSC).
Generate 15 high-yield Previous Year Style Questions (MCQs) covering History, Polity, Geography, Economy, Science, and Environment.
Translate all content into English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the schema.
"""

notes_prompt = """
Act as an expert Indian Competitive Exam Faculty.
Generate 10 detailed "1-Minute Cheat Sheets" (rapid revision notes with bullet points) covering key static topics like Constitutional Articles, History Timelines, River Systems, National Parks, and Science laws.
Translate all content into English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the schema.
"""

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

def generate_database(prompt, schema, filename):
    final_response = None
    for model_name in fallback_models:
        try:
            print(f"Attempting {filename} using model: {model_name}...")
            final_response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": schema, "temperature": 0.3}
            )
            if final_response and final_response.text:
                print(f"Successfully generated {filename} with {model_name}!")
                break
        except Exception as e:
            print(f"Model {model_name} failed for {filename}: {e}")
            continue

    if final_response and final_response.text:
        try:
            new_data = json.loads(final_response.text)
            existing_data = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    try: existing_data = json.load(f)
                    except: pass
            
            combined = new_data + existing_data
            combined = combined[:200] # Safe storage cap
            
            with open(filename, 'w') as f:
                json.dump(combined, f, indent=2)
            print(f"Successfully saved {len(new_data)} items to {filename}!")
        except Exception as parse_err:
            print(f"Error parsing JSON for {filename}: {parse_err}")
    else:
        print(f"Skipping {filename} due to temporary model limits.")

print("Starting database generation...")
generate_database(pyq_prompt, pyq_schema, 'pyq_bank.json')
generate_database(notes_prompt, notes_schema, 'cheat_sheets.json')
print("Database generation completed successfully!")
