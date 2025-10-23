"""
main.py
-------
Enhanced Legal Document Generator.
Generates professional legal documents using AI-powered content generation
with either reference document styling or predefined base styles.
"""

import os
import json
from gemini_extractor import extract_metadata_from_scenario, get_required_fields_for_document_type
from content_generator import generate_document_content_with_gemini
from document_builder import build_document_from_json_content
from validation_agent import validate_document_content
from config import OUTPUT_DIR, SCHEMA_DIR, SUPPORTED_DOC_TYPES


def main():
    print("=== Enhanced Legal Document Generator ===\n")

    # Step 1: Choose document type
    print("Available document types:")
    for doc_type in SUPPORTED_DOC_TYPES:
        print(f" - {doc_type}")
    
    doc_type = input("\nEnter document type: ").strip()
    if doc_type not in SUPPORTED_DOC_TYPES:
        print(f"❌ Unsupported document type '{doc_type}'. Using 'NDA' as default.")
        doc_type = "NDA"
    
    print(f"✅ Selected document type: {doc_type}")

    # Step 2: Enter scenario description
    print(f"\nEnter scenario description for {doc_type}:")
    scenario = input("> ").strip()
    
    if not scenario:
        print("❌ Scenario description is required.")
        return

    # Step 3: Extract metadata using Gemini
    print(f"\n🔍 Extracting metadata using Gemini...")
    extracted_data = extract_metadata_from_scenario(scenario, doc_type)

    # Step 4: Ask user for missing fields
    print(f"\n📄 Extracted Data:")
    for k, v in extracted_data.items():
        print(f"  {k}: {v if v else '[MISSING]'}")
    
    # Get document-specific required fields
    required_fields = get_required_fields_for_document_type(doc_type)
    for field in required_fields:
        if not extracted_data.get(field):
            extracted_data[field] = input(f"Please enter {field}: ").strip()

    print(f"\n✅ Final Data Used:")
    for k, v in extracted_data.items():
        print(f"  {k}: {v}")

    # Step 5: Ask for reference document (optional)
    reference_doc_path = None
    use_reference = input(f"\nDo you have a reference document to extract styles from? (y/n): ").strip().lower()
    
    if use_reference == 'y':
        ref_file = input("Enter template file name (without .docx): ").strip()
        # Always resolve templates directory relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reference_path = os.path.join(project_root, "templates", f"{ref_file}.docx")
        print(f"🔎 Checking for reference document at: {reference_path}")
        if os.path.exists(reference_path):
            reference_doc_path = reference_path
            print(f"✅ Reference document found: {reference_doc_path}")
        else:
            print(f"❌ Reference document not found: {reference_path}")
            print("🔄 Will use predefined styles instead")

    # Step 6: Generate full document content using Gemini
    print(f"\n🤖 Generating full document content using Gemini...")
    json_content = generate_document_content_with_gemini(doc_type, scenario, extracted_data)
    
    # Step 7: Validate and fix document content
    print(f"\n🔍 Validating document content...")
    
    # Load required fields for validation
    fields_file = os.path.join(SCHEMA_DIR, "doc_fields.json")
    required_fields = []
    if os.path.exists(fields_file):
        with open(fields_file, "r", encoding="utf-8") as f:
            fields_data = json.load(f)
            required_fields = fields_data.get(doc_type, {}).get("required_fields", [])
    
    # Validate content and fix any issues
    validated_content = validate_document_content(doc_type, json_content, required_fields)
    
    # Step 8: Save structured JSON output
    # Determine the best key for the filename
    doc_type_key_map = {
        "NDA": "Name",
        "Offer_Letter": "Name",
        "Contract": "Contract_Creation_Date"
    }
    name_key = doc_type_key_map.get(doc_type, None)
    name_val = None
    if name_key and name_key in extracted_data:
        name_val = extracted_data[name_key]
    elif doc_type == "Contract":
        # Fallback for Contract: try Start_Date, End_Date, Client_Name
        for alt_key in ["Start_Date", "End_Date", "Client_Name"]:
            if alt_key in extracted_data:
                name_val = extracted_data[alt_key]
                break
    else:
        # Fallback: use first required field that exists
        for field in required_fields:
            if field in extracted_data:
                name_val = extracted_data[field]
                break
    if not name_val:
        name_val = "Unknown"
    safe_name_val = str(name_val).replace(' ', '_')
    json_output_path = os.path.join(OUTPUT_DIR, "metadata", f"{doc_type}_content_{safe_name_val}.json")
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(validated_content, f, indent=2, ensure_ascii=False)

    print(f"📄 Structured JSON content saved: {json_output_path}")

    # Step 9: Build the final Word document
    print(f"\n📝 Building final Word document...")

    # Create a template for base structure
    from docx import Document
    import shutil
    temp_template = os.path.join(OUTPUT_DIR, "temp_template.docx")
    if reference_doc_path:
        # Copy reference doc and erase body content, keep header/footer
        shutil.copy(reference_doc_path, temp_template)
        doc = Document(temp_template)
        # Erase all body content (keep header/footer)
        doc._body.clear_content()
        doc.save(temp_template)
    else:
        doc = Document()
        doc.save(temp_template)

    final_filename = f"{safe_name_val}_{doc_type}_Final.docx"
    final_doc_path = build_document_from_json_content(
        template_path=temp_template,
        doc_type=doc_type,
        json_content=validated_content,
        output_filename=final_filename,
        reference_doc_path=reference_doc_path
    )

    # Clean up temp template
    if os.path.exists(temp_template):
        os.remove(temp_template)

    print(f"\n🎉 Document generation complete!")
    print(f"📄 Final document: {final_doc_path}")
    print(f"📋 JSON content: {json_output_path}")
    
    # Step 10: Show summary
    print(f"\n📊 Generation Summary:")
    print(f"  Document Type: {doc_type}")
    print(f"  Scenario: {scenario[:50]}{'...' if len(scenario) > 50 else ''}")
    print(f"  Reference Document: {'Yes' if reference_doc_path else 'No (used predefined styles)'}")
    print(f"  Sections Generated: {len(validated_content.get('sections', {}))}")
    print(f"  Validation: {'Passed' if validated_content == json_content else 'Fixed issues found'}")


if __name__ == "__main__":
    main()
