# src/persistence.py
"""
Persistence module
------------------
Handles saving and loading metadata, raw Gemini outputs,
and generated document information. Each document run
gets its own JSON record saved in output/metadata/.
"""

import os
import json
from datetime import datetime
from config import METADATA_OUTPUT_DIR, LOG_FILE

def _timestamp() -> str:
    """Generate a readable timestamp for filenames and logging."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def _metadata_file(name: str) -> str:
    """Constructs a metadata filename based on provided name and timestamp."""
    safe_name = name.replace(" ", "_")
    return os.path.join(METADATA_OUTPUT_DIR, f"{safe_name}_{_timestamp()}.json")

def save_metadata(doc_name: str, metadata: dict, raw_output: str | None = None):
    """
    Save parsed metadata and raw Gemini response to a JSON file.
    Includes timestamp and run info.
    """
    os.makedirs(METADATA_OUTPUT_DIR, exist_ok=True)

    record = {
        "document_name": doc_name,
        "timestamp": _timestamp(),
        "parsed_metadata": metadata,
        "raw_output": raw_output or "",
    }

    path = _metadata_file(doc_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    log_action(f"Metadata saved for '{doc_name}' → {os.path.basename(path)}")
    return path

def load_metadata(file_path: str) -> dict:
    """Load a metadata file from disk."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def log_action(message: str):
    """Append an action or event to the activity log."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {message}\n")

if __name__ == "__main__":
    # Test write and read
    test_data = {"Name": "Alice", "Company": "TechNova", "Date": "2025-10-15"}
    path = save_metadata("TestDoc", test_data, raw_output="raw Gemini output")
    print(f"✅ Saved metadata at {path}")
    loaded = load_metadata(path)
    print("Loaded:", loaded)
