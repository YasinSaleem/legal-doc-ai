

# === Imports ===
import streamlit as st
import os
import tempfile
# Third-party
from docx import Document
# Local modules
from config import SUPPORTED_DOC_TYPES, get_supported_languages
from translation_agent import TranslationAgent
from gemini_extractor import extract_metadata_from_scenario, get_required_fields_for_document_type
from content_generator import generate_document_content_with_gemini
from validation_agent import validate_document_content
from document_builder import build_document_from_json_content

st.set_page_config(page_title="Legal Document AI Generator", layout="centered")


# === App title and description ===
st.title("Legal Document AI Generator")
st.markdown("Generate professional legal documents using AI-powered content and styling.")

# === Step 1: Document type selection ===
doc_type = st.selectbox("Select document type:", SUPPORTED_DOC_TYPES, key="doc_type_select")

# === Step 1.5: Language selection ===
supported_languages = get_supported_languages()
language_options = [(code, name) for code, name in supported_languages.items()]
selected_language = st.selectbox("Select output language:", options=language_options, format_func=lambda x: x[1], key="output_language_select")
output_language_code = selected_language[0]

# === Step 2: Scenario input ===
scenario = st.text_area("Enter scenario description:", key="scenario_input")

# === Step 3: Reference document upload (optional) ===
reference_doc = st.file_uploader("Upload reference .docx template (optional)", type=["docx"], key="reference_doc_upload")

# === Session state initialization ===
if 'metadata' not in st.session_state:
    st.session_state['metadata'] = None
if 'user_fields' not in st.session_state:
    st.session_state['user_fields'] = {}
if 'final_doc_info' not in st.session_state:
    st.session_state['final_doc_info'] = None

required_fields = get_required_fields_for_document_type(doc_type)

# === Step 4: Submit scenario and extract metadata ===
if st.button("Submit Scenario", key="submit_scenario_btn"):
    if scenario:
        st.session_state['metadata'] = extract_metadata_from_scenario(scenario, doc_type)
        st.session_state['user_fields'] = {field: st.session_state['metadata'].get(field, "") for field in required_fields}
        st.success("Metadata extracted. Please fill in any missing fields below.")
    else:
        st.error("Please enter a scenario description.")

# === Step 5: Dynamic field completion (only show if metadata is extracted) ===
if st.session_state['metadata']:
    st.markdown("### Fill in missing fields:")
    for field in required_fields:
        st.session_state['user_fields'][field] = st.text_input(
            f"{field}", value=st.session_state['user_fields'].get(field, ""), key=f"field_{field}")

    # Only show Generate Document button if all fields are filled
    if all(st.session_state['user_fields'].values()):
        if st.button("Generate Document", key="generate_doc_btn"):
            # Prepare reference document path if uploaded
            ref_path = None
            if reference_doc:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp.write(reference_doc.read())
                    ref_path = tmp.name
            # Generate content
            json_content = generate_document_content_with_gemini(doc_type, scenario, st.session_state['user_fields'])
            # Validate content
            validated_content = validate_document_content(doc_type, json_content, required_fields)
            # Translate if needed
            if output_language_code != 'en':
                with st.spinner(f"Translating content to {supported_languages[output_language_code]}..."):
                    translator = TranslationAgent()
                    try:
                        validated_content = translator.translate_document_content(validated_content, output_language_code)
                        translation_status = f"Applied ({supported_languages[output_language_code]})"
                    except Exception as e:
                        st.warning(f"Translation failed: {e}. Continuing with English content.")
                        translation_status = "Failed, used English"
                        output_language_code = 'en'
            else:
                translation_status = "Not needed (English)"
            # Build document
            name_val = st.session_state['user_fields'][required_fields[0]] if required_fields else "Unknown"
            safe_name_val = str(name_val).replace(' ', '_')
            final_filename = f"{safe_name_val}_{doc_type}_{output_language_code.upper()}_Final.docx"
            with tempfile.TemporaryDirectory() as tmpdir:
                if ref_path:
                    template_path = ref_path
                else:
                    blank_template_path = os.path.join(tmpdir, "blank_template.docx")
                    Document().save(blank_template_path)
                    template_path = blank_template_path
                output_path = build_document_from_json_content(
                    template_path=template_path,
                    doc_type=doc_type,
                    json_content=validated_content,
                    output_filename=final_filename,
                    reference_doc_path=ref_path,
                    language_code=output_language_code
                )
                # Save info for summary
                st.session_state['final_doc_info'] = {
                    "final_doc_path": output_path,
                    "final_filename": final_filename,
                    "json_content": validated_content,
                    "doc_type": doc_type,
                    "output_language": supported_languages[output_language_code],
                    "scenario": scenario,
                    "reference_doc": bool(ref_path),
                    "sections_count": len(validated_content.get('sections', {})),
                    "translation_status": translation_status
                }
                # Read file for download
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="Download Final Document",
                        data=f.read(),
                        file_name=final_filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            st.success("Document generated successfully!")

    # Show summary after document generation
    if st.session_state.get('final_doc_info'):
        st.markdown("---")
        st.markdown("### Generation Summary")
        info = st.session_state['final_doc_info']
        st.write({
            "Document Type": info["doc_type"],
            "Output Language": info["output_language"],
            "Scenario": info["scenario"][:50] + ("..." if len(info["scenario"]) > 50 else ""),
            "Reference Document": "Yes" if info["reference_doc"] else "No (used predefined styles)",
            "Sections Generated": info["sections_count"],
            "Translation": info["translation_status"]
        })

