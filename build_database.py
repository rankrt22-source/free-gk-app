import os
import json
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY environment variable is not set.")

client = genai.Client(api_key=api_key)

pyq_prompt = """
Act as an expert Indian Competitive Exam Setter (UPSC, SSC CGL, State PSC).
Generate 15 high-yield Previous Year Style Questions (MCQs) covering History, Polity, Geography, Economy, Science, and Environment.
Each question must have exactly 4 options and one correct answer (index 0-3).
Translate all content into English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the schema.
"""

notes_prompt = """
Act as an expert Indian Competitive Exam Faculty.
Generate 10 detailed "1-Minute Cheat Sheets" (rapid revision notes with bullet points) covering key static topics like Constitutional Articles, History Timelines, River Systems, National Parks, and Science laws.
Translate all content into English (en), Hindi (hi), and Bengali (bn).
Output strictly as a JSON array matching the schema.
"""

lang_obj = {
    "type": "object",
    "properties": {"en": {"type": "string"}, "hi": {"type": "string"}, "bn": {"type": "string"}},
    "required": ["en", "hi", "bn"],
}

# Four options, each itself translated into en/hi/bn
lang_options_obj = {
    "type": "object",
    "properties": {
        "en": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
        "hi": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
        "bn": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
    },
    "required": ["en", "hi", "bn"],
}

pyq_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "Exam": {"type": "string"},
            "Subject": {"type": "string"},
            "Question": lang_obj,
            "Options": lang_options_obj,
            "CorrectAnswerIndex": {"type": "integer", "minimum": 0, "maximum": 3},
            "Explanation": lang_obj,
        },
        "required": ["Exam", "Subject", "Question", "Options", "CorrectAnswerIndex", "Explanation"],
    },
}

notes_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "Subject": {"type": "string"},
            "Time": {"type": "string"},
            "Title": lang_obj,
            "Content": lang_obj,
        },
        "required": ["Subject", "Time", "Title", "Content"],
    },
}

# Living models as of Aug 2026. gemini-2.0-flash and the whole gemini-1.5-*
# family return 404 (permanently shut down) — do not use them.
fallback_models = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]


def generate_database(prompt, schema, filename):
    final_response = None
    for model_name in fallback_models:
        try:
            print(f"Attempting {filename} using model: {model_name}...")
            final_response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                    "temperature": 0.3,
                },
            )
            if final_response and final_response.text:
                print(f"Successfully generated {filename} with {model_name}!")
                break
        except Exception as e:
            print(f"Model {model_name} failed for {filename}: {e}")
            continue

    if not (final_response and final_response.text):
        print(f"Skipping {filename}: all models failed.")
        return

    try:
        new_data = json.loads(final_response.text)
    except json.JSONDecodeError as e:
        print(f"Error parsing model JSON for {filename}: {e}")
        return

    existing_data = []
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: could not read existing {filename} ({e}); starting fresh.")

    combined = new_data + existing_data
    combined = combined[:200]  # Safe storage cap

    with open(filename, "w") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved {len(new_data)} new items to {filename} (total: {len(combined)})!")


print("Starting database generation...")
generate_database(pyq_prompt, pyq_schema, "pyq_bank.json")
generate_database(notes_prompt, notes_schema, "cheat_sheets.json")
print("Database generation completed successfully!")
