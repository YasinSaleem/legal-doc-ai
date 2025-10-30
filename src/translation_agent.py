"""
translation_agent.py
-------------------
Translates legal document content to multiple languages using
Hugging Face Transformers and MarianMT models.
"""

from transformers import pipeline, MarianMTModel, MarianTokenizer
import logging
from config import get_supported_languages

class TranslationAgent:
    def __init__(self):
        self.supported_languages = get_supported_languages()
        self.translators = {}  # Cache for loaded models
        logging.basicConfig(level=logging.INFO)
    
    def translate_document_content(self, content_json, target_language):
        """
        Translate all text content in document JSON to target language.
        Handles nested structure with title and sections.
        """
        if target_language == 'en':
            return content_json
        
        logging.info(f"🔄 Starting translation to {target_language}...")
        
        translated_content = {}
        
        # Translate title if present
        if 'title' in content_json:
            logging.info(f"Translating title...")
            translated_content['title'] = self._translate_text(
                content_json['title'], 
                target_language
            )
        
        # Translate sections
        if 'sections' in content_json:
            translated_content['sections'] = {}
            for section_key, section_data in content_json['sections'].items():
                logging.info(f"Translating section: {section_key}")
                
                translated_section = {
                    'type': section_data.get('type', 'Paragraph'),  # Keep type as-is
                    'content': self._translate_text(
                        section_data.get('content', ''),
                        target_language
                    )
                }
                translated_content['sections'][section_key] = translated_section
        
        logging.info(f"✅ Translation complete!")
        return translated_content
    
    def _translate_text(self, text, target_lang):
        """Translate individual text using MarianMT models"""
        if not text or text.strip() == "":
            return text
        
        try:
            model_name = f"Helsinki-NLP/opus-mt-en-{target_lang}"
            
            # Cache translator for reuse
            if model_name not in self.translators:
                logging.info(f"Loading translation model: {model_name}")
                self.translators[model_name] = pipeline(
                    "translation", 
                    model=model_name,
                    max_length=512
                )
            
            translator = self.translators[model_name]
            
            # Split long text into chunks if needed (MarianMT has token limits)
            max_length = 400
            if len(text) > max_length:
                # Split by sentences or paragraphs
                chunks = self._split_text(text, max_length)
                translated_chunks = []
                for chunk in chunks:
                    result = translator(chunk, max_length=512)
                    translated_chunks.append(result[0]['translation_text'])
                return ' '.join(translated_chunks)
            else:
                result = translator(text, max_length=512)
                return result[0]['translation_text']
            
        except Exception as e:
            logging.error(f"Translation failed for {target_lang}: {e}")
            logging.warning(f"Returning original text for: {text[:50]}...")
            return text  # Return original text if translation fails
    
    def _split_text(self, text, max_length):
        """Split text into chunks for translation"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
