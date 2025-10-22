# src/content_generator.py
"""
Content Generator
-----------------
Generates structured placeholder-based content for a given document type.
Uses Gemini to create sectioned text based on schemas defined in
schemas/doc_structure_schema.json.
"""

import json
import os
import google.generativeai as genai
from config import GEMINI_API_KEY, DEFAULT_MODEL, SCHEMA_DIR
from persistence import save_metadata, log_action

genai.configure(api_key=GEMINI_API_KEY)

def load_doc_structure_schema(doc_type: str) -> list[str]:
    """Load the structure schema for a given document type."""
    schema_path = os.path.join(SCHEMA_DIR, "doc_structure_schema.json")

    if not os.path.exists(schema_path):
        raise FileNotFoundError("❌ doc_structure_schema.json not found in schemas/")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    if doc_type not in schema:
        raise ValueError(f"❌ No schema defined for document type '{doc_type}'")

    return schema[doc_type]

def generate_content_placeholders(schema: list) -> list:
    """
    Generate placeholder content for each section in the schema.
    This function is called by main.py to create placeholder text.
    """
    placeholder_schema = []
    for section in schema:
        placeholder_schema.append({
            "type": section.get("type", "Paragraph"),
            "text": section.get("text", "[Content placeholder]")
        })
    return placeholder_schema

def generate_document_content_with_gemini(doc_type: str, scenario: str, extracted_data: dict) -> dict:
    """
    Use Gemini to generate full document content based on scenario and extracted data.
    Returns structured JSON with sections for easy styling application.
    """
    # Load the document structure schema
    structure = load_doc_structure_schema(doc_type)
    
    # Create a comprehensive prompt for Gemini
    prompt = f"""
    You are an expert legal document generator. Generate a complete {doc_type} document based on the following information:

    Document Type: {doc_type}
    Scenario: {scenario}
    Extracted Data: {extracted_data}

    Generate a professional, legally sound document with the following structure:
    {structure}

    Return the content as a JSON object where each key corresponds to a section from the structure,
    and the value contains the actual content for that section. Use the extracted data to fill in
    placeholders like [Name], [Company], [Date], etc.

    IMPORTANT FORMATTING RULES:
    1. Do NOT include the document title in the sections - only in the "title" field
    2. For signature sections, do NOT number them (e.g., use "Signatures" not "9. Signatures")
    3. Use proper legal document formatting with clear section numbering for main clauses
    4. Make sure all content is professional and legally appropriate
    5. For NDA: Only include Disclosing Party signature (single party)
    6. For Contract: Include both Disclosing Party and Receiving Party signatures (both parties)

    Format your response as valid JSON with this structure:
    {{
        "title": "Document Title",
        "sections": {{
            "section_name_1": {{
                "type": "Heading 1",
                "content": "Section content here"
            }},
            "section_name_2": {{
                "type": "Paragraph", 
                "content": "Section content here"
            }},
            "signatures": {{
                "type": "Signature",
                "content": "Disclosing Party: [Name]\\n\\n_____________________________"
            }}
        }}
    }}

    Make sure the content is professional, legally appropriate, and uses the provided data accurately.
    """

    model = genai.GenerativeModel(DEFAULT_MODEL)
    response = model.generate_content(prompt)
    raw_output = response.text.strip()

    print(f"\n[DEBUG] Gemini generated content:\n{raw_output}\n")

    try:
        # Clean and parse JSON
        text = clean_json_text(raw_output)
        generated_content = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[WARN] Could not parse Gemini response as JSON ({e}). Using fallback content.")
        # Fallback to template-based content
        generated_content = create_fallback_content(doc_type, extracted_data, structure)

    # Save the generated content
    save_metadata(f"{doc_type}_generated_content", generated_content, raw_output)
    log_action(f"Generated full document content for {doc_type} using Gemini.")
    
    return generated_content

def clean_json_text(text: str) -> str:
    """Remove Markdown or code block syntax from LLM response."""
    import re
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()

def create_fallback_content(doc_type: str, extracted_data: dict, structure: list) -> dict:
    """Create fallback content when Gemini parsing fails."""
    sections = {}
    for i, section in enumerate(structure):
        section_name = f"section_{i+1}"
        content = section.get("text", "")
        
        # Replace placeholders with actual data
        for key, value in extracted_data.items():
            content = content.replace(f"[{key}]", str(value))
        
        # Handle signature sections specially
        section_type = section.get("type", "Paragraph")
        if section_type == "Signature":
            # Format signature section properly - document type specific
            if doc_type.upper() == "NDA":
                # NDA: Single signature for Disclosing Party only
                content = f"Disclosing Party: {extracted_data.get('Name', '[Name]')}\n\n_____________________________"
            else:
                # Contract and other documents: Both parties
                content = f"Disclosing Party: {extracted_data.get('Name', '[Name]')}\n\n_____________________________\n\n\nReceiving Party: {extracted_data.get('Company', '[Company]')}\n\n_____________________________"
        
        sections[section_name] = {
            "type": section_type,
            "content": content
        }
    
    return {
        "title": f"{doc_type} Document",
        "sections": sections
    }

def generate_document_structure(doc_type: str, scenario: str) -> dict:
    """
    Generate structured content with placeholders for each section.
    """
    structure = load_doc_structure_schema(doc_type)

    prompt = f"""
    You are an AI document assistant.
    Based on the following scenario, generate a structured outline for a {doc_type}.
    
    Use placeholders like [Name], [Company], [Date] wherever applicable.

    Document structure sections:
    {structure}

    Respond in JSON format mapping each section name to its placeholder content.
    Scenario:
    {scenario}
    """

    model = genai.GenerativeModel(DEFAULT_MODEL)
    response = model.generate_content(prompt)
    raw_output = response.text.strip()

    try:
        structured_content = json.loads(raw_output)
    except json.JSONDecodeError:
        print("[WARN] Could not parse Gemini response as JSON, returning fallback content.")
        structured_content = {section: f"[{section} content here]" for section in structure}

    save_metadata(f"{doc_type}_structure", structured_content, raw_output)
    log_action(f"Generated structured content for {doc_type}.")
    return structured_content

if __name__ == "__main__":
    test_scenario = "Draft an NDA between Alice Johnson from TechNova Ltd for confidentiality terms."
    result = generate_document_structure("NDA", test_scenario)
    print(json.dumps(result, indent=2))
