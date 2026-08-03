import os
import json
import time
from google import genai
from google.genai import errors

# Initialize the Google Gen AI client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# -------------------------------------------------------------
# 1. SCHEMAS
# -------------------------------------------------------------
lang_obj = {
    "type": "object", 
    "properties": {
        "en": {"type": "string"}, 
        "hi": {"type": "string"}, 
        "bn": {"type": "string"}
    }, 
    "required": ["en", "hi", "bn"]
}

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

# -------------------------------------------------------------
# 2. ROBUST FETCHER WITH EXPONENTIAL BACKOFF
# -------------------------------------------------------------
def fetch_content_safely(prompt, schema, task_name):
    for model_name in fallback_models:
        retries = 3
        backoff = 10  # Start with a 10-second wait if rate-limited
        
        for attempt in range(retries):
            try:
                print(f"[{task_name}] Requesting {model_name} (Attempt {attempt+1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json", 
                        "response_schema": schema, 
                        "temperature": 0.4
                    }
                )
                
                if response and response.text:
                    new_data = json.loads(response.text)
                    
                    # Fix: Unwrap if AI accidentally nests the array inside a dict
                    if isinstance(new_data, dict):
                        for val in new_data.values():
                            if isinstance(val, list):
                                new_data = val
                                break
                    
                    # Fix: Ensure final output is strictly a list
                    if not isinstance(new_data, list):
                        new_data = [new_data] if new_data else []
                        
                    print(f"[{task_name}] Success! Fetched {len(new_data)} items.")
                    return new_data
                    
            except errors.APIError as e:
                error_msg = str(e).upper()
                # Catch Quota & Rate Limit errors gracefully
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    print(f"[{task_name}] Rate limit hit on {model_name}. Pausing for {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2  # Double the wait time for the next retry
                else:
                    print(f"[{task_name}] API Error on {model_name}: {e}")
                    break  # Break retry loop, try the next model in the fallback list
                    
            except Exception as e:
                print(f"[{task_name}] Unexpected JSON or parsing error: {e}")
                break
                
        print(f"[{task_name}] Switching to next model...")
    
    print(f"[{task_name}] All models exhausted. Returning empty array.")
    return []

# -------------------------------------------------------------
# 3. INCREMENTAL SAVER
# -------------------------------------------------------------
def append_and_save(filename, new_items):
    if not new_items:
        return
    
    existing_data = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception:
            pass
            
    # Prepend new items to the top and cap the file at 400 total items
    combined = new_items + existing_data
    combined = combined[:400]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"--> Saved! {filename} now contains {len(combined)} total items.")

# -------------------------------------------------------------
# 4. MAIN BULK GENERATION LOOPS
# -------------------------------------------------------------
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

print("=== STARTING PYQ BULK GENERATION ===")
for subj in subjects_pyq:
    prompt = f"""
    Act as an expert Indian Competitive Exam Setter (UPSC, SSC CGL).
    Generate 5 high-yield Previous Year Style Questions (MCQs) specifically for the subject: {subj}.
    Translate all content into English (en), Hindi (hi), and Bengali (bn).
    Output strictly as a JSON array matching the schema.
    """
    items = fetch_content_safely(prompt, pyq_schema, f"PYQ - {subj}")
    append_and_save('pyq_bank.json', items)
    time.sleep(8)  # Generous baseline pause to avoid rate limits

subjects_notes = [
    "Constitutional Articles & Schedules",
    "Important Governor-Generals & Viceroys",
    "River Systems & Mountain Passes",
    "Five-Year Plans & Economic Reforms",
    "National Parks & Ramsar Sites",
    "Physics/Chemistry Laws & Vitamins"
]

print("\n=== STARTING CHEAT SHEET BULK GENERATION ===")
for subj in subjects_notes:
    prompt = f"""
    Act as an expert Indian Competitive Exam Faculty.
    Generate 3 detailed '1-Minute Cheat Sheets' (rapid revision notes with bullet points) specifically for: {subj}.
    Translate all content into English (en), Hindi (hi), and Bengali (bn).
    Output strictly as a JSON array matching the schema.
    """
    items = fetch_content_safely(prompt, notes_schema, f"Notes - {subj}")
    append_and_save('cheat_sheets.json', items)
    time.sleep(8)

print("\n=== DATABASE BUILD CYCLE COMPLETED SUCCESSFULLY ===")
