import os
import json
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

comprehensive_pyq_prompt = """
Act as an expert Indian Competitive Exam Setter (UPSC, SSC CGL, State PSC).
Generate a diverse batch of 12 high-yield Previous Year Style Questions (MCQs) covering these exact critical domains:
1. Indian Art, Culture & Heritage (Temples, Dances, Architecture)
2. Ancient & Medieval Indian History
3. Modern Indian History & National Movement
4. Physical & Indian Geography (Mapping, Rivers, Monsoons)
5. Indian Polity (Fundamental Rights, DPSP, Judiciary, Amendments)
6. Indian Economy (Inflation, Banking, Fiscal Policy, Budget terms)
7. General Science & Technology (Space, Biotechnology, Physics)
8. Environment & Ecology (Climate Conventions, Red Data List species)

Translate all content into English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the schema.
"""

comprehensive_notes_prompt = """
Act as an expert Indian Competitive Exam Faculty.
Generate 10 detailed, high-yield "1-Minute Cheat Sheets" (rapid revision notes with bullet points) covering absolute must-know static topics for competitive exams:
1. Important Constitutional Articles & Schedules
2. Major Indus Valley & Vedic Civilization Sites
3. Important Governor-Generals & Viceroys of India
4. Major Mountain Passes & River Systems of India
5. Five-Year Plans and Economic Reforms of India
6. Important National Parks, Biosphere Reserves & Ramsar Sites
7. Important Physics & Chemistry Laws/Formules in Daily Life
8. Important Biological Diseases & Vitamins

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

def generate_full_exam_bank(prompt, schema, filename):
    for model_name in ["gemini-1.5-flash", "gemini-2.0-flash-lite"]:
        try:
            print(f"Generating full exam bank for {filename}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": schema, "temperature": 0.4}
            )
            new_data = json.loads(response.text)
            
            existing_data = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    try: existing_data = json.load(f)
                    except: pass
            
            # Keep up to 400 deep exam items
            combined = new_data + existing_data
            combined = combined[:400]
            
            with open(filename, 'w') as f:
                json.dump(combined, f, indent=2)
            print(f"Successfully expanded {filename}!")
            return True
        except Exception as e:
            print(f"Error with {model_name}: {e}")
            continue
    return False

generate_full_exam_bank(comprehensive_pyq_prompt, pyq_schema, 'pyq_bank.json')
generate_full_exam_bank(comprehensive_notes_prompt, notes_schema, 'cheat_sheets.json')
