import re

class TextPreprocessingPipeline:
    def __init__(self):
        pass
    
    def process(self, text, input_type="text", tone="formal", target_lang=None):
        """Main preprocessing pipeline for text-to-text translation"""
        # Basic text cleaning
        text = self.normalize_encoding(text)
        text = self.remove_disfluencies(text, input_type)
        text = self.mask_sensitive_data(text)
        text = self.apply_custom_glossary(text)
        text = self.normalize_units_and_numbers(text)
        return text.strip()
    
    def normalize_encoding(self, text):
        """Fix encoding issues"""
        return text.encode('utf-8', errors='replace').decode('utf-8')
    
    def remove_disfluencies(self, text, input_type):
        """Remove common speech disfluencies"""
        if input_type == "stt":
            disfluencies = [r"\buh+\b", r"\bum+\b", r"\byou know\b", r"\ber+\b", r"\bhmm+\b", r"\bokay\b"]
            pattern = re.compile("|".join(disfluencies), re.IGNORECASE)
            text = pattern.sub("", text)
        return re.sub(r"\s+", " ", text).strip()
    
    def mask_sensitive_data(self, text):
        """Mask emails and phone numbers"""
        text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL]", text)
        text = re.sub(r"\b\d{10,13}\b", "[PHONE]", text)
        return text
    
    def apply_custom_glossary(self, text):
        """Replace common terms with standard equivalents"""
        glossary = {
            "kms": "kilometers",
            "₹": "rupees",
            "circuit brkr": "circuit breaker",
            "break a leg": "good luck",
            "piece of cake": "very easy"
        }
        for k, v in glossary.items():
            text = text.replace(k, v)
        return text
    
    def normalize_units_and_numbers(self, text):
        """Basic unit normalization"""
        text = re.sub(r"(\d+)\s*kms?\b", r"\1 kilometers", text, flags=re.IGNORECASE)
        text = re.sub(r"₹\s*(\d+)", r"\1 rupees", text)
        return text