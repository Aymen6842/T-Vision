"""
Gemini LLM Handler for fallback intent understanding
Only used when rule-based parser is confused (<10% of cases)
"""

import os
import json
from typing import Dict, Optional
import google.generativeai as genai

class GeminiHandler:
    """Fallback LLM for unclear user intents"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini is configured"""
        return self.model is not None
    
    def understand_intent(self, user_message: str, context: Dict) -> Dict:
        """Ask Gemini to understand user's intent"""
        
        if not self.is_available():
            return {
                "success": False,
                "message": "I'm not sure what you mean. Could you rephrase that?"
            }
        
        try:
            prompt = self._build_prompt(user_message, context)
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            text = response.text.strip()
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            result = json.loads(text.strip())
            result["success"] = True
            return result
            
        except Exception as e:
            return {
                "success": False,
                "message": f"I'm having trouble understanding. Could you try again? (Error: {str(e)})"
            }
    
    def _build_prompt(self, user_message: str, context: Dict) -> str:
        """Build prompt for Gemini"""
        
        has_image = context.get("has_image", False)
        image_type = context.get("image_type", "unknown")
        
        return f"""You are helping a vision AI chatbot understand user requests.

**The chatbot's capabilities:**
1. Generate image captions (English or French)
2. Extract text via OCR
3. Recolor objects in photos (requires object name and color)
4. Create masks of objects (requires object name)

**Current context:**
- Has image uploaded: {has_image}
- Image type: {image_type}

**User said:** "{user_message}"

**Your task:**
Analyze what the user wants and respond in this EXACT JSON format:

{{
  "action": "caption|ocr|recolor|mask|unknown",
  "parameters": {{
    "object": "object name if needed",
    "color": "color name if needed",
    "language": "english|french if specified"
  }},
  "can_bot_do_it": true or false,
  "explanation": "brief explanation of what user wants"
}}

**Rules:**
- If user wants caption/OCR/recolor/mask → set can_bot_do_it to true
- If user wants something else (translate to Spanish, edit image, etc) → set can_bot_do_it to false
- Extract object and color names if mentioned
- Default language is english unless user specifies french

Respond ONLY with the JSON, no other text."""
    
    def generate_polite_refusal(self, explanation: str) -> str:
        return (f"Ah, I understand now - {explanation}. "
                f"Unfortunately, that's beyond my current abilities. 😅\n\n"
                f"I can help with:\n"
                f"• Captions (English or French)\n"
                f"• OCR/text extraction\n"
                f"• Recoloring objects\n"
                f"• Creating masks")
