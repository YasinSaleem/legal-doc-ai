# Legal Document AI - API Server

This FastAPI server exposes the legal document generation functionality through REST endpoints.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment:**
Make sure your `.env` file contains:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

3. **Start the server:**
```bash
cd src
python api_server.py
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/api/docs
- **ReDoc Documentation**: http://localhost:8000/api/redoc

## API Endpoints

### 1. Generate Document (Main Endpoint)
```
POST /api/v1/documents/generate
```

**Form Data Parameters:**
- `doc_type` (required): Document type (NDA, Contract, MOU, Offer_Letter, IP_Agreement)
- `language` (optional): Language code (en, hi, es, fr, de, it, pt, ru, ja, ko, ar, zh)
- `scenario` (required): Natural language scenario description
- `template` (optional): Upload a .docx template file

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/generate" \
  -F "doc_type=NDA" \
  -F "language=en" \
  -F "scenario=Draft an NDA between Alice Johnson from TechNova Ltd for confidentiality terms regarding software development project discussions."
```

**Response:**
```json
{
  "success": true,
  "download_url": "/downloads/abc123_Alice_Johnson_NDA_EN_Final.docx",
  "metadata": {
    "doc_type": "NDA",
    "language": "English",
    "processing_time_ms": 15000,
    "sections_generated": 5,
    "extracted_fields": {...},
    ...
  }
}
```

### 2. Get Configuration
```
GET /api/v1/config
```

Returns supported document types and languages.

### 3. Get Document Fields
```
GET /api/v1/config/fields/{doc_type}
```

Returns required fields for a specific document type.

## Frontend Integration

### JavaScript Example:
```javascript
async function generateDocument() {
  const formData = new FormData();
  formData.append('doc_type', 'NDA');
  formData.append('language', 'en');
  formData.append('scenario', 'Your scenario here...');
  
  // Optional: Add template file
  const templateFile = document.getElementById('template').files[0];
  if (templateFile) {
    formData.append('template', templateFile);
  }
  
  try {
    const response = await fetch('/api/v1/documents/generate', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Download the document
      window.location.href = result.download_url;
      console.log('Generated:', result.metadata);
    } else {
      console.error('Generation failed:', result.error);
    }
  } catch (error) {
    console.error('Request failed:', error);
  }
}
```

### Python Client Example:
```python
import requests

def generate_document(doc_type, scenario, language="en", template_path=None):
    url = "http://localhost:8000/api/v1/documents/generate"
    
    data = {
        'doc_type': doc_type,
        'language': language,
        'scenario': scenario
    }
    
    files = {}
    if template_path:
        files['template'] = open(template_path, 'rb')
    
    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
        
        result = response.json()
        if result['success']:
            print(f"Document generated: {result['download_url']}")
            print(f"Processing time: {result['metadata']['processing_time_ms']}ms")
            return result
        else:
            print(f"Generation failed: {result['error']}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    finally:
        if template_path and 'template' in files:
            files['template'].close()

# Example usage
generate_document(
    doc_type="NDA",
    scenario="Draft an NDA between Alice Johnson from TechNova Ltd...",
    language="en"
)
```

## Error Handling

The API returns structured error responses:

```json
{
  "success": false,
  "error": "Error description",
  "error_type": "DocumentGenerationError"
}
```

Common error codes:
- `400`: Bad Request (invalid parameters, missing scenario, etc.)
- `404`: File not found (for download endpoints)
- `500`: Internal Server Error

## File Management

- Generated documents are automatically cleaned up after 1 hour
- Files are served from `/downloads/` endpoint
- Template files are processed in memory and not stored permanently

## Production Deployment

For production deployment:

1. **Configure CORS** properly in `api_server.py`
2. **Add authentication** if needed
3. **Use a proper database** instead of in-memory file storage
4. **Add rate limiting** and monitoring
5. **Use HTTPS** and proper security headers
6. **Deploy with gunicorn** or similar WSGI server

Example production command:
```bash
gunicorn api_server:app -w 4 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:8000
```