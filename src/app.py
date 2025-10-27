
import streamlit as st
from config import SUPPORTED_DOC_TYPES
from gemini_extractor import extract_metadata_from_scenario, get_required_fields_for_document_type
from content_generator import generate_document_content_with_gemini
from validation_agent import validate_document_content
from document_builder import build_document_from_json_content
import os
import tempfile

st.set_page_config(page_title="Legal Document AI Generator", layout="centered")
st.title("Legal Document AI Generator")
st.markdown("Generate professional legal documents using AI-powered content and styling.")

# Step 1: Document type selection
doc_type = st.selectbox("Select document type:", SUPPORTED_DOC_TYPES)

# Step 2: Scenario input
scenario = st.text_area("Enter scenario description:")

# Step 3: Reference document upload (optional)
reference_doc = st.file_uploader("Upload reference .docx template (optional)", type=["docx"])


# Session state for metadata and user_fields
if 'metadata' not in st.session_state:
    st.session_state['metadata'] = None
if 'user_fields' not in st.session_state:
    st.session_state['user_fields'] = {}

required_fields = get_required_fields_for_document_type(doc_type)

# Step 4: Submit scenario and extract metadata
if st.button("Submit Scenario"):
    if scenario:
        st.session_state['metadata'] = extract_metadata_from_scenario(scenario, doc_type)
        st.session_state['user_fields'] = {field: st.session_state['metadata'].get(field, "") for field in required_fields}
        st.success("Metadata extracted. Please fill in any missing fields below.")
    else:
        st.error("Please enter a scenario description.")

# Step 5: Dynamic field completion (only show if metadata is extracted)
if st.session_state['metadata']:
    st.markdown("### Fill in missing fields:")
    for field in required_fields:
        st.session_state['user_fields'][field] = st.text_input(
            f"{field}", value=st.session_state['user_fields'].get(field, ""))

    # Only show Generate Document button if all fields are filled
    if all(st.session_state['user_fields'].values()):
        if st.button("Generate Document"):
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
            # Build document
            final_filename = f"{st.session_state['user_fields'][required_fields[0]].replace(' ', '_')}_{doc_type}_Final.docx"
            from docx import Document
            with tempfile.TemporaryDirectory() as tmpdir:
                if ref_path:
                    template_path = ref_path
                else:
                    # Create a blank Word document as template
                    blank_template_path = os.path.join(tmpdir, "blank_template.docx")
                    Document().save(blank_template_path)
                    template_path = blank_template_path
                output_path = build_document_from_json_content(
                    template_path=template_path,
                    doc_type=doc_type,
                    json_content=validated_content,
                    output_filename=final_filename,
                    reference_doc_path=ref_path
                )
                # Read file for download
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="Download Final Document",
                        data=f.read(),
                        file_name=final_filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            st.success("Document generated successfully!")
    else:
        st.info("Please fill in all required fields to enable document generation.")
