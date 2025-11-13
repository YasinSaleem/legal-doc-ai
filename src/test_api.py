"""
test_api.py
----------
Simple test script to verify the API server works correctly.
"""

import requests
import json
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Health check passed: {data['message']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_get_config():
    """Test the configuration endpoint"""
    print("🔍 Testing configuration endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/config")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Config retrieved:")
        print(f"   Document types: {data['document_types']}")
        print(f"   Languages: {list(data['languages'].keys())}")
        return data
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return None

def test_get_fields():
    """Test the document fields endpoint"""
    print("🔍 Testing document fields endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/config/fields/NDA")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Fields for NDA: {data['required_fields']}")
        return data
    except Exception as e:
        print(f"❌ Fields test failed: {e}")
        return None

def test_generate_document():
    """Test document generation endpoint"""
    print("🔍 Testing document generation endpoint...")
    
    # Test data
    test_data = {
        'doc_type': 'NDA',
        'language': 'en',
        'scenario': 'Draft an NDA between Alice Johnson from TechNova Ltd for confidentiality terms regarding software development project discussions. The agreement should be valid for 2 years in California jurisdiction.'
    }
    
    try:
        print(f"📤 Sending request with data: {test_data}")
        response = requests.post(f"{BASE_URL}/api/v1/documents/generate", data=test_data)
        
        print(f"📨 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Document generation successful!")
            print(f"   Download URL: {data['download_url']}")
            print(f"   Processing time: {data['metadata']['processing_time_ms']}ms")
            print(f"   Sections generated: {data['metadata']['sections_generated']}")
            print(f"   Final filename: {data['metadata']['final_filename']}")
            
            # Test download
            download_url = f"{BASE_URL}{data['download_url']}"
            print(f"🔍 Testing download from: {download_url}")
            
            download_response = requests.get(download_url)
            if download_response.status_code == 200:
                print(f"✅ Download successful! File size: {len(download_response.content)} bytes")
                
                # Save test file
                test_filename = f"test_generated_{data['metadata']['final_filename']}"
                with open(test_filename, 'wb') as f:
                    f.write(download_response.content)
                print(f"💾 Test file saved as: {test_filename}")
                
            else:
                print(f"❌ Download failed: {download_response.status_code}")
            
            return data
        else:
            print(f"❌ Generation failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Document generation test failed: {e}")
        return None

def main():
    """Run all tests"""
    print("🚀 Starting API tests...")
    print("=" * 50)
    
    # Check if server is running
    if not test_health_check():
        print("❌ Server is not running. Please start the API server first:")
        print("   cd src && python api_server.py")
        return
    
    print()
    
    # Test configuration
    config = test_get_config()
    if not config:
        return
    
    print()
    
    # Test fields
    fields = test_get_fields()
    if not fields:
        return
    
    print()
    
    # Test document generation
    result = test_generate_document()
    
    print()
    print("=" * 50)
    if result:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("❌ Some tests failed. Check the API server logs.")

if __name__ == "__main__":
    main()