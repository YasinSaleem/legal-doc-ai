"""
api_server.py
------------
FastAPI server that exposes legal document generation functionality through REST API.
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from document_service import (
    generate_complete_document, 
    DocumentGenerationError, 
    get_document_types, 
    get_supported_languages_list, 
    get_required_fields
)
from api_models import (
    GenerateDocumentResponse, 
    ErrorResponse, 
    ConfigResponse, 
    FieldsResponse,
    DocumentMetadata
)


# Create FastAPI app
app = FastAPI(
    title="Legal Document AI Generator API",
    description="Generate professional legal documents using AI-powered content and styling",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create downloads directory
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Mount static files for document downloads
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# Store for generated files (in production, use Redis or database)
generated_files = {}


def cleanup_file(file_path: str, file_id: str):
    """Background task to cleanup temporary files"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        generated_files.pop(file_id, None)
        print(f"🗑️  Cleaned up file: {file_path}")
    except Exception as e:
        print(f"⚠️  Error cleaning up file {file_path}: {e}")


@app.get("/", summary="Health Check")
async def root():
    """Health check endpoint"""
    return {"message": "Legal Document AI Generator API is running"}


@app.get("/api/v1/config", response_model=ConfigResponse, summary="Get Configuration")
async def get_config():
    """Get supported document types and languages"""
    try:
        return ConfigResponse(
            document_types=get_document_types(),
            languages=get_supported_languages_list()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/config/fields/{doc_type}", response_model=FieldsResponse, summary="Get Document Fields")
async def get_document_fields(doc_type: str):
    """Get required fields for a specific document type"""
    try:
        required_fields = get_required_fields(doc_type)
        return FieldsResponse(
            doc_type=doc_type,
            required_fields=required_fields,
            optional_fields=[]  # Could be extended to include optional fields
        )
    except DocumentGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/documents/generate", response_model=GenerateDocumentResponse, summary="Generate Document")
async def generate_document(
    background_tasks: BackgroundTasks,
    doc_type: str = Form(..., description="Document type (NDA, Contract, etc.)"),
    language: str = Form(default="en", description="Language code (en, hi, es, etc.)"),
    scenario: str = Form(..., description="Natural language scenario description"),
    template: Optional[UploadFile] = File(None, description="Optional document template (.docx)")
):
    """
    Generate a complete legal document from scenario description.
    
    This endpoint processes the entire pipeline:
    1. Extracts metadata from scenario
    2. Generates document content
    3. Validates content
    4. Translates if needed
    5. Builds final Word document
    """
    try:
        # Validate inputs
        if not scenario.strip():
            raise HTTPException(status_code=400, detail="Scenario description cannot be empty")
        
        if len(scenario) < 10:
            raise HTTPException(status_code=400, detail="Scenario description must be at least 10 characters")
        
        # Validate document type
        supported_doc_types = get_document_types()
        if doc_type not in supported_doc_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported document type '{doc_type}'. Supported types: {supported_doc_types}"
            )
        
        # Validate language
        supported_languages = get_supported_languages_list()
        if language not in supported_languages:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported language '{language}'. Supported languages: {list(supported_languages.keys())}"
            )
        
        # Process template file if provided
        template_content = None
        template_filename = None
        
        if template:
            if not template.filename.endswith('.docx'):
                raise HTTPException(status_code=400, detail="Template file must be a .docx file")
            
            template_content = await template.read()
            template_filename = template.filename
        
        print(f"🚀 API Request: Generating {doc_type} document in {language}")
        print(f"📄 Template: {'Yes' if template else 'No'}")
        print(f"📝 Scenario: {scenario[:100]}...")
        
        # Generate document
        doc_path, metadata = generate_complete_document(
            doc_type=doc_type,
            language=language,
            scenario=scenario,
            template_file_content=template_content,
            template_filename=template_filename
        )
        
        # Move generated file to downloads directory
        file_id = str(uuid.uuid4())
        filename = os.path.basename(doc_path)
        download_path = DOWNLOADS_DIR / f"{file_id}_{filename}"
        
        # Copy file to downloads directory
        import shutil
        shutil.move(doc_path, download_path)
        
        # Store file info for cleanup
        generated_files[file_id] = {
            "path": str(download_path),
            "filename": filename,
            "metadata": metadata
        }
        
        # Schedule cleanup after 1 hour (3600 seconds) - commented out for testing
        # background_tasks.add_task(cleanup_file, str(download_path), file_id)
        
        # Create download URL
        download_url = f"/downloads/{file_id}_{filename}"
        
        # Convert metadata to response model
        metadata_model = DocumentMetadata(**metadata)
        
        return GenerateDocumentResponse(
            download_url=download_url,
            metadata=metadata_model
        )
        
    except DocumentGenerationError as e:
        print(f"❌ Document generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/downloads/{filename}")
async def download_file(filename: str):
    """Download a generated document by filename"""
    file_path = DOWNLOADS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.exception_handler(DocumentGenerationError)
async def document_generation_exception_handler(request, exc):
    """Handle document generation errors"""
    return ErrorResponse(
        error=str(exc),
        error_type="DocumentGenerationError"
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return ErrorResponse(
        error="An unexpected error occurred",
        error_type="InternalServerError"
    )


if __name__ == "__main__":
    print("🚀 Starting Legal Document AI API Server...")
    print("📖 API Documentation: http://localhost:8000/api/docs")
    print("🔄 Auto-reload enabled for development")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )