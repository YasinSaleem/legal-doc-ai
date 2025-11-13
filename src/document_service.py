"""
document_service.py
------------------
Service layer that wraps all document generation functionality
into a single service function for API consumption.
"""

import os
import tempfile
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from docx import Document

from gemini_extractor import extract_metadata_from_scenario, get_required_fields_for_document_type
from content_generator import generate_document_content_with_gemini
from validation_agent import validate_document_content
from translation_agent import TranslationAgent
from document_builder import build_document_from_json_content
from config import SUPPORTED_DOC_TYPES, get_supported_languages, OUTPUT_DIR


class DocumentGenerationError(Exception):
    """Custom exception for document generation errors"""
    pass


def generate_complete_document(
    doc_type: str,
    language: str,
    scenario: str,
    template_file_content: Optional[bytes] = None,
    template_filename: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Complete document generation pipeline.
    
    Args:
        doc_type: Type of document (NDA, Contract, etc.)
        language: Target language code (en, hi, es, etc.)
        scenario: Natural language scenario description
        template_file_content: Optional template file content in bytes
        template_filename: Optional template filename
    
    Returns:
        Tuple of (document_file_path, metadata_dict)
    
    Raises:
        DocumentGenerationError: If any step in the pipeline fails
    """
    start_time = datetime.now()
    
    try:
        # Validate inputs
        if doc_type not in SUPPORTED_DOC_TYPES:
            raise DocumentGenerationError(f"Unsupported document type: {doc_type}")
        
        supported_languages = get_supported_languages()
        if language not in supported_languages:
            raise DocumentGenerationError(f"Unsupported language: {language}")
        
        if not scenario.strip():
            raise DocumentGenerationError("Scenario description cannot be empty")
        
        print(f"🚀 Starting document generation for {doc_type} in {supported_languages[language]}")
        
        # Step 1: Extract metadata from scenario
        print("📋 Step 1: Extracting metadata from scenario...")
        extracted_data = extract_metadata_from_scenario(scenario, doc_type)
        
        # Step 2: Get required fields and attempt to fill missing ones
        print("🔍 Step 2: Processing required fields...")
        required_fields = get_required_fields_for_document_type(doc_type)
        
        # Check for missing required fields and try to generate reasonable defaults
        missing_fields = []
        for field in required_fields:
            if not extracted_data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️  Missing fields detected: {missing_fields}")
            # For now, we'll use placeholder values. In production, you might want to 
            # make another Gemini call to infer these or return an error
            for field in missing_fields:
                if field == "Date":
                    extracted_data[field] = datetime.now().strftime("%Y-%m-%d")
                elif field == "Term":
                    extracted_data[field] = "2 years"
                elif field == "Jurisdiction":
                    extracted_data[field] = "United States"
                else:
                    extracted_data[field] = f"[Please provide {field}]"
        
        # Step 3: Generate document content
        print("🤖 Step 3: Generating document content with Gemini...")
        json_content = generate_document_content_with_gemini(doc_type, scenario, extracted_data)
        
        # Step 4: Validate content
        print("🔍 Step 4: Validating document content...")
        validated_content = validate_document_content(doc_type, json_content, required_fields)
        
        # Step 5: Translate if needed
        if language != 'en':
            print(f"🌍 Step 5: Translating content to {supported_languages[language]}...")
            translator = TranslationAgent()
            try:
                validated_content = translator.translate_document_content(validated_content, language)
                translation_status = f"Applied ({supported_languages[language]})"
            except Exception as e:
                print(f"⚠️  Translation failed: {e}. Continuing with English content.")
                translation_status = "Failed, used English"
                language = 'en'
        else:
            translation_status = "Not needed (English)"
        
        # Step 6: Prepare template
        print("📄 Step 6: Preparing document template...")
        template_path = None
        
        if template_file_content and template_filename:
            # Save uploaded template to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                tmp_file.write(template_file_content)
                template_path = tmp_file.name
        else:
            # Create blank template
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                Document().save(tmp_file.name)
                template_path = tmp_file.name
        
        # Step 7: Build final document
        print("📝 Step 7: Building final Word document...")
        
        # Generate safe filename
        name_val = extracted_data.get("Name") or extracted_data.get("Client_Name") or "Document"
        safe_name_val = str(name_val).replace(' ', '_').replace('/', '_').replace('\\', '_')
        final_filename = f"{safe_name_val}_{doc_type}_{language.upper()}_Final.docx"
        
        try:
            final_doc_path = build_document_from_json_content(
                template_path=template_path,
                doc_type=doc_type,
                json_content=validated_content,
                output_filename=final_filename,
                reference_doc_path=template_path if template_file_content else None,
                language_code=language
            )
        finally:
            # Clean up temporary template file
            if template_path and os.path.exists(template_path):
                os.remove(template_path)
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Step 8: Prepare metadata
        metadata = {
            "doc_type": doc_type,
            "language": supported_languages[language],
            "language_code": language,
            "extracted_fields": extracted_data,
            "sections_generated": len(validated_content.get('sections', {})),
            "processing_time_ms": processing_time_ms,
            "template_used": bool(template_file_content),
            "template_filename": template_filename,
            "translation_status": translation_status,
            "scenario": scenario[:100] + ("..." if len(scenario) > 100 else ""),
            "generation_timestamp": end_time.isoformat(),
            "missing_fields_filled": missing_fields,
            "final_filename": final_filename
        }
        
        print(f"✅ Document generation completed successfully!")
        print(f"📄 Final document: {final_doc_path}")
        print(f"⏱️  Processing time: {processing_time_ms}ms")
        
        return final_doc_path, metadata
        
    except Exception as e:
        error_msg = f"Document generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        raise DocumentGenerationError(error_msg) from e


def get_document_types() -> list:
    """Get list of supported document types"""
    return SUPPORTED_DOC_TYPES


def get_supported_languages_list() -> dict:
    """Get dictionary of supported languages"""
    return get_supported_languages()


def get_required_fields(doc_type: str) -> list:
    """Get required fields for a specific document type"""
    if doc_type not in SUPPORTED_DOC_TYPES:
        raise DocumentGenerationError(f"Unsupported document type: {doc_type}")
    
    return get_required_fields_for_document_type(doc_type)


if __name__ == "__main__":
    # Test the service
    test_scenario = "Draft an NDA between Alice Johnson from TechNova Ltd for confidentiality terms."
    
    try:
        doc_path, metadata = generate_complete_document(
            doc_type="NDA",
            language="en", 
            scenario=test_scenario
        )
        print(f"\n✅ Test successful!")
        print(f"Document: {doc_path}")
        print(f"Metadata: {metadata}")
    except DocumentGenerationError as e:
        print(f"\n❌ Test failed: {e}")