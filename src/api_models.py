"""
api_models.py
------------
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types"""
    NDA = "NDA"
    OFFER_LETTER = "Offer_Letter"
    CONTRACT = "Contract"
    MOU = "MOU"
    IP_AGREEMENT = "IP_Agreement"


class LanguageCode(str, Enum):
    """Supported language codes"""
    ENGLISH = "en"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    CHINESE = "zh"


class GenerateDocumentRequest(BaseModel):
    """Request model for document generation"""
    doc_type: DocumentType = Field(..., description="Type of document to generate")
    language: LanguageCode = Field(default=LanguageCode.ENGLISH, description="Target language for the document")
    scenario: str = Field(..., min_length=10, description="Natural language scenario description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_type": "NDA",
                "language": "en",
                "scenario": "Draft an NDA between Alice Johnson from TechNova Ltd for confidentiality terms regarding software development project discussions."
            }
        }


class DocumentMetadata(BaseModel):
    """Metadata about the generated document"""
    doc_type: str
    language: str
    language_code: str
    extracted_fields: Dict[str, Any]
    sections_generated: int
    processing_time_ms: int
    template_used: bool
    template_filename: Optional[str] = None
    translation_status: str
    scenario: str
    generation_timestamp: str
    missing_fields_filled: List[str]
    final_filename: str


class GenerateDocumentResponse(BaseModel):
    """Response model for successful document generation"""
    success: bool = True
    download_url: str = Field(..., description="URL to download the generated document")
    metadata: DocumentMetadata = Field(..., description="Metadata about the generation process")


class ErrorResponse(BaseModel):
    """Response model for errors"""
    success: bool = False
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")


class ConfigResponse(BaseModel):
    """Response model for configuration endpoints"""
    document_types: List[str]
    languages: Dict[str, str]


class FieldsResponse(BaseModel):
    """Response model for document fields endpoint"""
    doc_type: str
    required_fields: List[str]
    optional_fields: Optional[List[str]] = []