# Legal Document AI Generator

An intelligent system that generates professional legal documents using AI-powered content generation and advanced styling capabilities. This system leverages Google Gemini AI to create structured, professionally formatted legal documents with automatic validation and quality assurance.

## 🎯 Project Overview

This system automates the creation of legal documents through a multi-agent architecture that handles everything from metadata extraction to final document formatting. It supports multiple document types with customizable styling and validation.

## 📁 Project Structure

```
legal-doc-ai/
├── src/                          # Core source code and AI agents
├── schemas/                      # Document structure and field definitions
├── styles/                       # Styling configurations for each document type
├── templates/                    # User-uploaded document templates
├── base_templates/               # System default templates
├── output/                       # Generated documents and metadata
├── working/                      # Temporary processing files
├── logs/                         # System activity logs
├── requirements.txt              # Python dependencies
├── env_example.txt               # Environment configuration template
└── README.md                     # This documentation
```

## 🤖 AI Agents & Core Components

### **1. Main Orchestrator**
- **File**: `src/main.py`
- **Purpose**: Central coordinator that manages the entire document generation workflow
- **Responsibilities**:
  - User interaction and input collection
  - Workflow orchestration between all agents
  - Final document assembly and output management

### **2. Gemini Metadata Extractor**
- **File**: `src/gemini_extractor.py`
- **Purpose**: Extracts structured metadata from natural language scenarios
- **Key Functions**:
  - `extract_metadata_from_scenario()`: Parses user scenarios to extract key information
  - `clean_json_text()`: Cleans AI responses for proper JSON parsing
- **Extracted Fields**: Name, Company, Date, Term, Jurisdiction

### **3. Content Generation Agent**
- **File**: `src/content_generator.py`
- **Purpose**: Uses Gemini AI to generate full document content based on scenarios and metadata
- **Key Functions**:
  - `generate_document_content_with_gemini()`: Creates complete document content
  - `generate_content_placeholders()`: Generates placeholder content for templates
  - `create_fallback_content()`: Creates backup content when AI parsing fails
- **Features**: Document-type specific content generation with professional legal language

### **4. Document Builder Agent**
- **File**: `src/document_builder.py`
- **Purpose**: Assembles Word documents from structured content with proper formatting
- **Key Functions**:
  - `build_document_from_json_content()`: Creates final Word documents
  - `add_signature_section()`: Handles document-specific signature layouts
  - `add_nda_signature()`: Single-party signatures for NDAs
  - `add_contract_signature()`: Dual-party signatures for contracts with invisible borders
  - `apply_style_to_paragraph()`: Applies formatting to document elements

### **5. Style Extraction Agent**
- **File**: `src/style_extractor.py`
- **Purpose**: Extracts and manages document styling from templates and reference documents
- **Key Functions**:
  - `extract_styles_from_template()`: Extracts fonts, formatting, and layout from Word documents
  - `load_style_json()`: Loads document-specific style configurations
  - `get_default_styles()`: Provides fallback styling when custom styles aren't available

### **6. Template Manager Agent**
- **File**: `src/template_manager.py`
- **Purpose**: Manages document templates and working copies
- **Key Functions**:
  - `list_available_templates()`: Lists all available templates
  - `find_template()`: Locates templates by name
  - `prepare_working_copy()`: Creates working copies for processing
  - `register_new_template()`: Adds new user templates to the system

### **7. Validation Agent**
- **File**: `src/validation_agent.py`
- **Purpose**: Validates document content and fixes placeholder issues
- **Key Functions**:
  - `validate_document_content()`: Main validation orchestrator
  - `find_placeholders_in_content()`: Detects remaining placeholders in content
  - `fix_placeholders_with_gemini()`: Uses AI to fix content issues
  - `validate_document_structure()`: Ensures document compliance with type requirements

### **8. Configuration Manager**
- **File**: `src/config.py`
- **Purpose**: Manages system configuration, environment variables, and directory structure
- **Key Functions**:
  - `ensure_directories_exist()`: Creates required directory structure
  - Environment variable management
  - Path configuration for all system components

### **9. Persistence Manager**
- **File**: `src/persistence.py`
- **Purpose**: Handles data persistence, logging, and metadata storage
- **Key Functions**:
  - `save_metadata()`: Saves document metadata and AI responses
  - `log_action()`: Records system activities
  - `load_metadata()`: Retrieves stored metadata

## 📋 Configuration Files & Directories

### **Schemas Directory (`schemas/`)**
Contains JSON files that define document structure and field requirements:

#### **`doc_structure_schema.json`**
- **Purpose**: Defines the structure and content templates for each document type
- **Contains**: Section definitions with types (Heading, Paragraph, Signature) and placeholder content
- **Example Structure**:
```json
{
  "NDA": [
    {"type": "Heading 1", "text": "Non-Disclosure Agreement"},
    {"type": "Paragraph", "text": "This Agreement is between [Name] and [Company]..."},
    {"type": "Signature", "text": "Disclosing Party: [Name]"}
  ]
}
```

#### **`doc_fields.json`**
- **Purpose**: Defines required and optional fields for each document type
- **Contains**: Field validation rules and requirements
- **Example Structure**:
```json
{
  "NDA": {
    "required_fields": ["Name", "Company", "Date", "Term", "Jurisdiction"],
    "optional_fields": ["Confidential_Info_Description", "Governing_Law"]
  }
}
```

### **Styles Directory (`styles/`)**
Contains JSON files that define formatting and styling for each document type:

#### **`nda_style.json`**
- **Purpose**: Defines styling for NDA documents
- **Contains**: Font specifications, alignment, spacing, and formatting rules

#### **`contract_style.json`**
- **Purpose**: Defines styling for Contract documents
- **Contains**: Professional formatting with justified paragraphs and proper headings

#### **`offer_letter_style.json`**
- **Purpose**: Defines styling for Offer Letter documents
- **Contains**: Business letter formatting and professional appearance

**Style Configuration Example**:
```json
{
  "Heading 1": {
    "font": "Calibri Light",
    "size": 16,
    "bold": true,
    "align": "center",
    "spacing": 1.0
  },
  "Paragraph": {
    "font": "Times New Roman",
    "size": 12,
    "align": "justify",
    "spacing": 1.0
  }
}
```

### **Templates Directory (`templates/`)**
- **Purpose**: Stores user-uploaded Word document templates
- **Usage**: Users can add custom `.docx` templates for style extraction
- **Processing**: Templates are copied to working directory for processing

### **Base Templates Directory (`base_templates/`)**
- **Purpose**: Contains system default templates
- **Usage**: Fallback templates when no user templates are available
- **Processing**: Used as base structure for document generation

### **Output Directory (`output/`)**
Contains all generated documents and metadata:

#### **`output/docs/`**
- **Purpose**: Stores final Word documents
- **Naming**: `{Name}_{DocumentType}_Final.docx`
- **Format**: Professional .docx files with proper formatting

#### **`output/metadata/`**
- **Purpose**: Stores JSON content, AI responses, and processing logs
- **Contents**:
  - Generated content JSON files
  - AI response logs
  - Metadata extraction results
  - Validation reports

### **Working Directory (`working/`)**
- **Purpose**: Temporary processing files and working copies
- **Usage**: Intermediate files during document generation
- **Cleanup**: Automatically cleaned up after processing

### **Logs Directory (`logs/`)**
- **Purpose**: System activity logs and debugging information
- **Contents**: Processing logs, error reports, and system activities

## 🚀 Installation & Setup

### **1. Prerequisites**
- Python 3.8 or higher
- Google Gemini API key
- Internet connection for AI processing

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Environment Configuration**
```bash
# Copy the example environment file
cp env_example.txt .env

# Edit .env and add your Gemini API key
# Get your API key from: https://makersuite.google.com/app/apikey
```

### **4. Verify Setup**
```bash
cd src
python -c "from config import ensure_directories_exist; ensure_directories_exist(); print('✅ Setup complete!')"
```

## 📖 Usage Guide

### **Basic Usage**
```bash
cd src
python main.py
```

### **Workflow Steps**

1. **Document Type Selection**: Choose from NDA, Contract, or Offer Letter
2. **Scenario Input**: Provide natural language description of requirements
3. **Metadata Extraction**: AI extracts key information from scenario
4. **Content Generation**: AI creates full document content
5. **Validation**: System validates and fixes any placeholder issues
6. **Document Assembly**: Final Word document is created with proper formatting
7. **Output**: Documents saved to `output/docs/` and metadata to `output/metadata/`

### **Example Usage**

**NDA Generation**:
```
Document Type: NDA
Scenario: "Create an NDA between Alice Johnson from TechNova Ltd and XYZ Corp for 3 years covering software development discussions"
Reference Document: /path/to/custom_template.docx (optional)
```

**Contract Generation**:
```
Document Type: Contract
Scenario: "Draft a service agreement between Client Corp and Service Provider Inc for web development services at $5000/month"
Reference Document: None (uses predefined styles)
```

## 🔧 Customization

### **Adding New Document Types**
1. Update `SUPPORTED_DOC_TYPES` in `src/config.py`
2. Add structure definition in `schemas/doc_structure_schema.json`
3. Add field requirements in `schemas/doc_fields.json`
4. Create style configuration in `styles/{type}_style.json`
5. Update validation rules in `src/validation_agent.py`

### **Modifying Document Structures**
Edit `schemas/doc_structure_schema.json` to change document layouts:
```json
{
  "Your_Document_Type": [
    {"type": "Heading 1", "text": "Document Title"},
    {"type": "Paragraph", "text": "Your content here with [placeholders]"}
  ]
}
```

### **Customizing Styles**
Modify style files in `styles/` directory to change appearance:
```json
{
  "Heading 1": {
    "font": "Your Font",
    "size": 18,
    "bold": true,
    "align": "center"
  }
}
```

## 🎨 Document Features

### **NDA Documents**
- Single-party signatures (Disclosing Party only)
- Date field below signature
- Jurisdiction as required field
- Professional confidentiality language

### **Contract Documents**
- Dual-party signatures (both parties side-by-side)
- Invisible table borders for clean appearance
- Date field spanning both signature columns
- Comprehensive service agreement terms

### **Offer Letter Documents**
- Professional business letter format
- Position and compensation details
- Acceptance and signature sections
- HR-friendly formatting

## 🔍 Validation & Quality Assurance

### **Automatic Validation**
- Placeholder detection and fixing
- Document structure compliance
- Required field validation
- Content quality assurance

### **AI-Powered Fixes**
- Gemini AI automatically fixes placeholder issues
- Content enhancement and professional language
- Structure validation and compliance checking

## 🛠️ Troubleshooting

### **Common Issues**

1. **"GEMINI_API_KEY not found"**
   - Ensure `.env` file exists with valid API key
   - Get API key from: https://makersuite.google.com/app/apikey

2. **"Schema not found"**
   - Check `schemas/doc_structure_schema.json` exists
   - Verify document type in `SUPPORTED_DOC_TYPES`

3. **Style extraction fails**
   - System automatically falls back to predefined styles
   - Check reference documents are valid `.docx` files

4. **Placeholder issues**
   - Validation agent automatically detects and fixes placeholders
   - Check logs in `output/metadata/` for details

### **Debug Mode**
```bash
export DEBUG=1
python main.py
```

## 📊 Output Formats

### **Word Documents**
- Professional .docx files with proper formatting
- Document-specific signature layouts
- Justified paragraphs and professional styling
- Saved to `output/docs/`

### **JSON Metadata**
- Structured content with organized sections
- AI response logs and processing information
- Validation reports and quality metrics
- Saved to `output/metadata/`

## 🔄 System Architecture

The system follows a modular agent-based architecture where each component has specific responsibilities:

1. **Input Processing**: User input collection and validation
2. **AI Processing**: Metadata extraction and content generation
3. **Validation**: Quality assurance and placeholder fixing
4. **Document Assembly**: Word document creation with proper formatting
5. **Output Management**: File organization and metadata storage

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your enhancements
4. Test thoroughly with different document types
5. Submit a pull request with detailed description

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs in `output/metadata/` and `logs/`
3. Check system configuration in `src/config.py`
4. Create an issue with detailed error information and logs
