import os
import json
from google import genai

# 1. Initialize Client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. Comprehensive Prompts covering ALL core competitive exam subjects
pyq_prompt = """
Act as an expert Indian Competitive Exam Faculty (UPSC, SSC CGL, State PCS).
Generate a massive, diverse bank of 10 high-yield Previous Year Style Questions (MCQs) covering ALL of these core subjects:
1. Indian Polity & Governance
2. Modern Indian History & National Movement
3. Indian & World Geography
4. Indian Economy & Budget
5. General Science (Physics, Chemistry, Biology)
6. Environment, Ecology & Biodiversity

Generate content in English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the required schema.
"""

notes_prompt = """
Act as an expert Indian Competitive Exam Faculty.
Generate a comprehensive bank of 8 detailed "1-Minute Cheat Sheets" (quick revision notes) covering ALL of these core subjects:
1. Indian Polity
2. Modern History
3. Geography
4. Economy
5. General Science
6. Environment

Generate content in English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the required schema.
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

# 4. Model Resolver
available_models = []
try:
    for m in client.models.list():
        clean_name = m.name.replace('models/', '')
        if 'gemini' in clean_name and 'embed' not in clean_name:
            available_models.append(clean_name)
except Exception:
    available_models = ["gemini-1.5-flash", "gemini-2.0-flash-lite"]

def generate_massive_database(prompt, schema, filename):
    for model_name in available_models:
        try:
            print(f"Generating massive batch for {filename} using {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": schema, "temperature": 0.5}
            )
            
            new_data = json.loads(response.text)
            
            existing_data = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    try:
                        existing_data = json.load(f)
                    except: pass
            
            # Combine and expand database up to 300 items
            combined_data = new_data + existing_data
            combined_data = combined_data[:300]
            
            with open(filename, 'w') as f:
                json.dump(combined_data, f, indent=2)
                
            print(f"Successfully updated {filename} with {len(new_data)} new items!")
            return True
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue
    print(f"Failed to generate {filename}")
    return False

# 5. Execute Full Generation
print("Starting full database generation across all subjects...")
generate_massive_database(pyq_prompt, pyq_schema, 'pyq_bank.json')
generate_massive_database(notes_prompt, notes_schema, 'cheat_sheets.json')
