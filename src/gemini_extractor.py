# src/gemini_extractor.py
"""
Gemini Metadata Extractor
-------------------------
Extracts structured metadata (Name, Company, Date, etc.)
from a given natural language scenario description.

If any field is missing, the model leaves it blank.
All extracted data (parsed + raw) are stored for auditing.
"""

import json
import re
import warnings
import os
import google.generativeai as genai

from config import GEMINI_API_KEY, DEFAULT_MODEL
from persistence import save_metadata, log_action

# Suppress unnecessary logs
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)

# Expected metadata fields (extendable via schemas later)
EXPECTED_FIELDS = ["Name", "Company", "Date", "Term", "Jurisdiction"]

def get_required_fields_for_document_type(doc_type: str) -> list:
    """Get required fields for a specific document type."""
    try:
        import os
        import json
        from config import SCHEMA_DIR
        
        fields_file = os.path.join(SCHEMA_DIR, "doc_fields.json")
        if os.path.exists(fields_file):
            with open(fields_file, "r", encoding="utf-8") as f:
                fields_data = json.load(f)
                return fields_data.get(doc_type, {}).get("required_fields", ["Name", "Company", "Date"])
        else:
            # Fallback to basic fields if schema file doesn't exist
            return ["Name", "Company", "Date"]
    except Exception as e:
        print(f"⚠️ Error loading fields for {doc_type}: {e}")
        return ["Name", "Company", "Date"]

def clean_json_text(text: str) -> str:
    """Remove Markdown or code block syntax from LLM response."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()

def extract_metadata_from_scenario(scenario: str, doc_type: str = "General") -> dict:
    """
    Extract structured metadata from a scenario using Gemini.
    Returns a dict with missing fields blank.
    """
    # Load document-specific required fields
    required_fields = get_required_fields_for_document_type(doc_type)
    
    # Create dynamic field list for prompt
    field_list = "\n".join([f"- {field}" for field in required_fields])
    
    # Create dynamic JSON format
    json_format = "{\n" + ",\n".join([f'  "{field}": "string"' for field in required_fields]) + "\n}"
    
    prompt = f"""
    You are an intelligent assistant that extracts key details from a document drafting scenario.

    Extract the following fields if present:
    {field_list}

    If any of them are missing, leave them blank ("").

    Respond ONLY with valid JSON in this format:
    {json_format}

    Scenario:
    {scenario}
    """

    model = genai.GenerativeModel(DEFAULT_MODEL)
    response = model.generate_content(prompt)
    raw_output = response.text.strip()

    print("\n[DEBUG] Gemini raw output:\n", raw_output, "\n")

    # Clean formatting and try parsing JSON
    text = clean_json_text(raw_output)
    try:
        data = json.loads(text)
    except Exception as e:
        print(f"[WARN] Could not parse Gemini output as JSON ({e}).")
        data = {field: "" for field in required_fields}

    # Ensure all required fields for this document type exist
    for field in required_fields:
        data.setdefault(field, "")

    # Save parsed + raw metadata
    save_metadata(f"{doc_type}_metadata", data, raw_output)

    log_action(f"Extracted metadata for {doc_type}: {data}")
    return data

if __name__ == "__main__":
    test_scenario = "Draft an NDA between Alice Johnson from TechNova Ltd dated October 22, 2025."
    result = extract_metadata_from_scenario(test_scenario, doc_type="NDA")
    print("✅ Extracted Metadata:\n", json.dumps(result, indent=2))
