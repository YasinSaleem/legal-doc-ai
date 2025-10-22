"""
template_manager.py
-------------------
Manages templates for Legal-Doc-AI.

Responsibilities:
- List and locate base/user templates
- Handle template selection and preparation for editing
- Register new templates and extract their styling
"""

import os
import shutil
from config import TEMPLATE_DIR, BASE_TEMPLATE_DIR, WORKING_DIR, STYLE_DIR
from style_extractor import extract_styles_from_template


def list_available_templates() -> list:
    """
    Return a list of all available templates (both base and user-uploaded).
    """
    templates = []

    for folder in [BASE_TEMPLATE_DIR, TEMPLATE_DIR]:
        for file in os.listdir(folder):
            if file.lower().endswith(".docx"):
                templates.append(file)

    return sorted(set(templates))


def find_template(template_name: str) -> str | None:
    """
    Search for a template (case-insensitive) in base and user template folders.
    Returns absolute path if found, else None.
    """
    target = f"{template_name.lower()}.docx"

    # Search both user and base directories
    for folder in [TEMPLATE_DIR, BASE_TEMPLATE_DIR]:
        for file in os.listdir(folder):
            if file.lower() == target:
                return os.path.join(folder, file)
    return None


def prepare_working_copy(template_name: str) -> str | None:
    """
    Create a working copy of a template in the /working directory.
    This ensures the original remains untouched.
    """
    source_path = find_template(template_name)
    if not source_path:
        print(f"❌ Template '{template_name}.docx' not found.")
        return None

    os.makedirs(WORKING_DIR, exist_ok=True)
    working_path = os.path.join(WORKING_DIR, f"{template_name.lower()}_working.docx")

    shutil.copy2(source_path, working_path)
    print(f"📄 Working copy prepared: {working_path}")
    return working_path


def register_new_template(template_path: str, doc_type: str) -> None:
    """
    Register a new user-uploaded template.
    Copies it into the templates folder and extracts its styles.
    """
    if not os.path.exists(template_path):
        print("❌ Provided template path does not exist.")
        return

    # Destination
    dest_path = os.path.join(TEMPLATE_DIR, f"{doc_type.lower()}.docx")
    shutil.copy2(template_path, dest_path)
    print(f"✅ Template registered as '{doc_type.lower()}.docx' in templates folder.")

    # Extract styles
    style_output_path = os.path.join(STYLE_DIR, f"{doc_type.lower()}_style.json")
    extract_styles_from_template(dest_path, style_output_path)
    print(f"🎨 Styles extracted and stored at: {style_output_path}")


# ──────────────────────────────────────────────
# Example manual test
# ──────────────────────────────────────────────
# if __name__ == "__main__":
#     print("=== Template Manager Test ===")
#     print("Available templates:", list_available_templates())

#     name = input("Enter template name to find: ").strip()
#     path = find_template(name)

#     if path:
#         print(f"✅ Template found: {path}")
#         prepare_working_copy(name)
#     else:
#         print("❌ No matching template found.")
