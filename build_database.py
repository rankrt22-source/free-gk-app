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

def generate_single_run_bank(prompt, schema, filename):
    existing_data = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try: existing_data = json.load(f)
            except: pass

    final_response = None
    for model_name in fallback_models:
        try:
            print(f"Generating comprehensive {filename} in a single run using {model_name}...")
            final_response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": schema, "temperature": 0.4}
            )
            if final_response and final_response.text:
                break
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue

    if final_response and final_response.text:
        try:
            new_data = json.loads(final_response.text)
            combined = new_data + existing_data
            combined = combined[:400] # Cap total stored items at 400
            with open(filename, 'w') as f:
                json.dump(combined, f, indent=2)
            print(f"Successfully generated and saved {len(new_data)} items to {filename} in one run!")
        except Exception as parse_err:
            print(f"Error parsing response for {filename}: {parse_err}")
    else:
        print(f"Failed to generate {filename} in this run.")

pyq_prompt = """
Act as an expert Indian Competitive Exam Setter (UPSC, SSC CGL, State PSC).
Generate a massive, exhaustive batch of 25 high-yield Previous Year Style Questions (MCQs) covering every core domain:
1. Indian Art, Culture & Heritage
2. Ancient, Medieval & Modern History
3. Physical, Indian & World Geography
4. Indian Polity & Governance
5. Indian Economy & Budget
6. General Science & Technology
7. Environment & Ecology
Translate all content into English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the schema.
"""

notes_prompt = """
Act as an expert Indian Competitive Exam Faculty.
Generate a massive, exhaustive batch of 20 detailed "1-Minute Cheat Sheets" (rapid revision notes with bullet points) covering every core domain:
1. Constitutional Articles & Schedules
2. Civilization Sites & Historical Timelines
3. Important Viceroys & National Movements
4. River Systems & Mountain Passes
5. Five-Year Plans & Economic Reforms
6. National Parks & Ramsar Sites
7. Physics/Chemistry formulas & Biological Vitamins
Translate all content into English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the schema.
"""

print("Executing single-run comprehensive database generation...")
generate_single_run_bank(pyq_prompt, pyq_schema, 'pyq_bank.json')
generate_single_run_bank(notes_prompt, notes_schema, 'cheat_sheets.json')
