"""
style_extractor.py
------------------
Responsible for extracting, storing, and loading paragraph-level
style information (fonts, alignment, spacing, etc.) from Word templates.

Supports:
- Extracting styles from .docx templates (python-docx)
- Saving and loading style profiles as JSON per document type
- Providing fallback to default base styles
"""

import json
import os
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from config import STYLE_DIR


# ──────────────────────────────────────────────
# Helper: Map alignment to readable text
# ──────────────────────────────────────────────
ALIGNMENT_MAP = {
    WD_ALIGN_PARAGRAPH.LEFT: "left",
    WD_ALIGN_PARAGRAPH.CENTER: "center",
    WD_ALIGN_PARAGRAPH.RIGHT: "right",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
    None: "left"
}


def extract_styles_from_template(template_path: str, save_path: str) -> None:
    """
    Extract paragraph-level style info from a Word template (.docx)
    and save as JSON to `save_path`.
    """
    print(f"📝 Extracting styles from template: {template_path}")

    doc = Document(template_path)
    style_data = {}

    # Iterate through each paragraph
    for para in doc.paragraphs:
        style_name = para.style.name

        # Skip duplicates
        if style_name in style_data:
            continue

        # Get font details from the paragraph's run (if exists)
        if para.runs:
            run = para.runs[0]
            font = run.font
            font_name = font.name or "Default"
            font_size = font.size.pt if font.size else 12
            bold = font.bold if font.bold is not None else False
            italic = font.italic if font.italic is not None else False
            underline = font.underline if font.underline is not None else False
        else:
            font_name, font_size, bold, italic, underline = "Default", 12, False, False, False

        # Alignment and spacing
        alignment = ALIGNMENT_MAP.get(para.alignment, "left")
        spacing = para.paragraph_format.line_spacing or 1.0
        left_indent = para.paragraph_format.left_indent.pt if para.paragraph_format.left_indent else 0
        right_indent = para.paragraph_format.right_indent.pt if para.paragraph_format.right_indent else 0

        style_data[style_name] = {
            "font": font_name,
            "size": font_size,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "align": alignment,
            "spacing": spacing,
            "indent_left": left_indent,
            "indent_right": right_indent
        }

    # Ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Ensure essential style mappings exist by adding default mappings for missing essential styles
    essential_styles = get_default_styles()
    for essential_style_name, default_props in essential_styles.items():
        if essential_style_name not in style_data:
            print(f"⚠️ Essential style '{essential_style_name}' not found in template, adding default mapping")
            style_data[essential_style_name] = default_props

    # Save style info
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(style_data, f, indent=2)

    print(f"✅ Styles extracted and saved to: {save_path}")


def load_style_json(doc_type: str) -> dict:
    """
    Load a style configuration for a specific document type.
    Falls back to default styles if not found.
    """
    style_path = os.path.join(STYLE_DIR, f"{doc_type.lower()}_style.json")

    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            print(f"🎨 Loaded custom style for '{doc_type}'")
            return json.load(f)
    else:
        print(f"⚠️ No custom style for '{doc_type}' found. Using base style.")
        return get_default_styles()


def get_default_styles() -> dict:
    """
    Return a predefined default style configuration
    (used when no document-specific style file exists).
    """
    return {
        "Heading 1": {"font": "Calibri Light", "size": 16, "bold": True, "italic": False, "align": "center", "spacing": 1.0},
        "Heading 2": {"font": "Calibri", "size": 14, "bold": True, "italic": False, "align": "left", "spacing": 1.0},
        "Normal": {"font": "Times New Roman", "size": 12, "bold": False, "italic": False, "align": "justify", "spacing": 1.0},
        "Paragraph": {"font": "Times New Roman", "size": 12, "bold": False, "italic": False, "align": "justify", "spacing": 1.0},
        "Signature": {"font": "Times New Roman", "size": 12, "bold": False, "italic": False, "align": "left", "spacing": 1.5}
    }


# ──────────────────────────────────────────────
# Example manual test
# ──────────────────────────────────────────────
# if __name__ == "__main__":
#     test_template = "templates/template.docx"
#     output_style_json = os.path.join(STYLE_DIR, "test_style.json")

#     if os.path.exists(test_template):
#         extract_styles_from_template(test_template, output_style_json)
#     else:
#         print("❌ No test template found.")
