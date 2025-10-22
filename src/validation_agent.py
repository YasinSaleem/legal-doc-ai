"""
validation_agent.py
------------------
Validation agent that checks final document content for:
1. Proper document type compliance
2. Missing placeholders that need to be filled
3. Required fields validation
4. Content quality assurance
"""

import json
import re
import google.generativeai as genai
from config import GEMINI_API_KEY, DEFAULT_MODEL
from persistence import save_metadata, log_action


def validate_document_content(doc_type: str, content: dict, required_fields: list) -> dict:
    """
    Validate the final document content and fix any issues.
    
    Args:
        doc_type: Type of document (NDA, Contract, etc.)
        content: The generated content dictionary
        required_fields: List of required fields for this document type
    
    Returns:
        dict: Validated and corrected content
    """
    print(f"\n🔍 Validating {doc_type} document content...")
    
    # Check for placeholders in the content
    placeholder_issues = find_placeholders_in_content(content)
    
    if placeholder_issues:
        print(f"⚠️ Found {len(placeholder_issues)} placeholder issues:")
        for issue in placeholder_issues:
            print(f"  - {issue}")
        
        # Fix placeholders using Gemini
        corrected_content = fix_placeholders_with_gemini(doc_type, content, placeholder_issues, required_fields)
        
        # Validate again after correction
        final_validation = validate_document_structure(doc_type, corrected_content)
        
        if final_validation["is_valid"]:
            print("✅ Document validation passed after corrections")
            return corrected_content
        else:
            print("❌ Document validation failed even after corrections")
            return content
    else:
        # No placeholders found, validate structure
        validation_result = validate_document_structure(doc_type, content)
        
        if validation_result["is_valid"]:
            print("✅ Document validation passed")
            return content
        else:
            print(f"❌ Document validation failed: {validation_result['issues']}")
            return content


def find_placeholders_in_content(content: dict) -> list:
    """Find any remaining placeholders in the content."""
    placeholder_pattern = r"\[([^\]]+)\]"
    issues = []
    
    # Check title
    if "title" in content:
        matches = re.findall(placeholder_pattern, content["title"])
        for match in matches:
            issues.append(f"Title contains placeholder: [{match}]")
    
    # Check sections
    if "sections" in content:
        for section_name, section_data in content["sections"].items():
            section_content = section_data.get("content", "")
            matches = re.findall(placeholder_pattern, section_content)
            for match in matches:
                issues.append(f"Section '{section_name}' contains placeholder: [{match}]")
    
    return issues


def fix_placeholders_with_gemini(doc_type: str, content: dict, placeholder_issues: list, required_fields: list) -> dict:
    """Use Gemini to fix placeholder issues in the content."""
    print(f"🤖 Using Gemini to fix {len(placeholder_issues)} placeholder issues...")
    
    # Create a prompt for Gemini to fix the issues
    prompt = f"""
    You are a legal document expert. Fix the following {doc_type} document by addressing placeholder issues.
    
    Current document content:
    {json.dumps(content, indent=2)}
    
    Issues found:
    {placeholder_issues}
    
    Required fields for {doc_type}: {required_fields}
    
    Instructions:
    1. Remove any placeholders that are not required fields
    2. For required fields that have placeholders, either:
       - Fill them with appropriate generic text if the field is missing
       - Remove the placeholder and its surrounding text if it's not essential
    3. Ensure the document remains legally sound and professional
    4. Maintain proper document structure and formatting
    
    Return the corrected content in the same JSON format.
    """
    
    try:
        model = genai.GenerativeModel(DEFAULT_MODEL)
        response = model.generate_content(prompt)
        raw_output = response.text.strip()
        
        # Clean and parse JSON
        text = clean_json_text(raw_output)
        corrected_content = json.loads(text)
        
        # Save the correction attempt
        save_metadata(f"{doc_type}_validation_correction", corrected_content, raw_output)
        log_action(f"Fixed placeholder issues in {doc_type} document")
        
        return corrected_content
        
    except Exception as e:
        print(f"⚠️ Failed to fix placeholders with Gemini: {e}")
        return content


def validate_document_structure(doc_type: str, content: dict) -> dict:
    """Validate that the document structure is appropriate for the document type."""
    issues = []
    
    # Check if title exists
    if "title" not in content or not content["title"]:
        issues.append("Document title is missing")
    
    # Check if sections exist
    if "sections" not in content or not content["sections"]:
        issues.append("Document sections are missing")
    
    # Check for document-specific requirements
    if doc_type == "NDA":
        issues.extend(validate_nda_structure(content))
    elif doc_type == "Contract":
        issues.extend(validate_contract_structure(content))
    elif doc_type == "Offer_Letter":
        issues.extend(validate_offer_letter_structure(content))
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues
    }


def validate_nda_structure(content: dict) -> list:
    """Validate NDA-specific structure requirements."""
    issues = []
    sections = content.get("sections", {})
    
    # Check for essential NDA sections
    essential_sections = ["confidential information", "obligations", "term", "signatures"]
    section_texts = [section.get("content", "").lower() for section in sections.values()]
    
    for essential in essential_sections:
        if not any(essential in text for text in section_texts):
            issues.append(f"Missing essential NDA section: {essential}")
    
    return issues


def validate_contract_structure(content: dict) -> list:
    """Validate Contract-specific structure requirements."""
    issues = []
    sections = content.get("sections", {})
    
    # Check for essential Contract sections
    essential_sections = ["services", "payment", "term", "signatures"]
    section_texts = [section.get("content", "").lower() for section in sections.values()]
    
    for essential in essential_sections:
        if not any(essential in text for text in section_texts):
            issues.append(f"Missing essential Contract section: {essential}")
    
    return issues


def validate_offer_letter_structure(content: dict) -> list:
    """Validate Offer Letter-specific structure requirements."""
    issues = []
    sections = content.get("sections", {})
    
    # Check for essential Offer Letter sections
    essential_sections = ["position", "compensation", "acceptance", "signatures"]
    section_texts = [section.get("content", "").lower() for section in sections.values()]
    
    for essential in essential_sections:
        if not any(essential in text for text in section_texts):
            issues.append(f"Missing essential Offer Letter section: {essential}")
    
    return issues


def clean_json_text(text: str) -> str:
    """Remove Markdown or code block syntax from LLM response."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()


if __name__ == "__main__":
    # Test validation
    test_content = {
        "title": "Test NDA",
        "sections": {
            "intro": {
                "type": "Paragraph",
                "content": "This is a test NDA between [Name] and [Company]."
            }
        }
    }
    
    result = validate_document_content("NDA", test_content, ["Name", "Company", "Date"])
    print("Validation result:", result)
