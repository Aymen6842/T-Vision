"""
Smart rule-based intent parser for chatbot
Handles 90% of cases without needing Gemini
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Intent:
    """Parsed user intent"""
    action: Optional[str]  # caption, ocr, recolor, mask, count, greeting
    parameters: Dict[str, str]
    confidence: float  # 0.0 to 1.0
    missing_params: List[str]

class IntentParser:
    """Rule-based natural language parsing"""
    
    # Comprehensive color list
    COLORS = [
        "red", "blue", "green", "yellow", "purple", "orange",
        "pink", "black", "white", "brown", "gray", "grey",
        "cyan", "magenta", "violet", "indigo", "turquoise",
        "lime", "navy", "maroon", "teal", "olive", "silver", "gold"
    ]
    
    # Stop words to ignore when extracting objects
    STOP_WORDS = {
        "the", "a", "an", "to", "make", "recolor", "color", "colour",
        "paint", "change", "mask", "segment", "caption", "describe",
        "tell", "me", "about", "this", "that", "it", "can", "you",
        "please", "in", "with", "of", "for", "want", "would", "like",
        "create", "generate", "give", "show", "i", "my", "is", "are",
        "how", "many", "count", "number", "do", "does", "see", "find", "look"
    }
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.color_pattern = re.compile(
            r'\b(' + '|'.join(self.COLORS) + r')\b',
            re.IGNORECASE
        )
    
    def parse(self, message: str, current_state: str = "idle") -> Intent:
        """Parse user message into intent"""
        msg_lower = message.lower().strip()
        
        # Detect action
        action, action_confidence = self._detect_action(msg_lower)
        
        # Extract parameters
        params = self._extract_parameters(msg_lower, action)
        
        # Determine missing parameters
        missing = self._get_missing_params(action, params)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(action, params, action_confidence)
        
        return Intent(
            action=action,
            parameters=params,
            confidence=confidence,
            missing_params=missing
        )
    
    def _detect_action(self, message: str) -> Tuple[Optional[str], float]:
        """Detect what action user wants"""
        
        # Greetings
        greeting_keywords = ["hi", "hello", "hey", "good morning", "good afternoon"]
        # Valid greeting if message is short and contains keyword
        if len(message) < 20 and any(kw == message or message.startswith(kw + " ") for kw in greeting_keywords):
            return "greeting", 0.95
        
        # Caption keywords
        caption_keywords = ["caption", "describe", "tell me about", "what is this",
                           "what's in", "explain", "describe image"]
        if any(kw in message for kw in caption_keywords):
            return "caption", 0.9
        
        # OCR keywords
        ocr_keywords = ["ocr", "read", "text", "extract text", "what does it say",
                       "read the text", "extract"]
        if any(kw in message for kw in ocr_keywords):
            return "ocr", 0.9
        
        # Recolor keywords
        recolor_keywords = ["recolor", "color", "colour", "paint", "change color",
                           "make it", "turn it"]
        if any(kw in message for kw in recolor_keywords):
            # Extra confidence if we see color + potential object
            if self._find_color(message) or "color" in message:
                return "recolor", 0.95
            return "recolor", 0.7
        
        # Mask keywords
        mask_keywords = ["mask", "segment", "outline", "select", "isolate"]
        if any(kw in message for kw in mask_keywords):
            return "mask", 0.85
            
        # Count/Detection keywords "do you see", "how many"
        count_keywords = ["how many", "count", "number of", "do you see", "is there a", "are there any"]
        if any(kw in message for kw in count_keywords):
            return "count", 0.9
        
        # Ambiguous or greeting
        if len(message) < 20 and any(w in message for w in ["help", "what", "how"]):
            return None, 0.3
        
        return None, 0.0
    
    def _extract_parameters(self, message: str, action: Optional[str]) -> Dict[str, str]:
        """Extract parameters like color, object, language"""
        params = {}
        
        # Extract color
        color = self._find_color(message)
        if color:
            params["color"] = color
        
        # Extract language preference
        if any(w in message for w in ["english", "anglais", "in english"]):
            params["language"] = "english"
        elif any(w in message for w in ["french", "français", "francais", "in french"]):
            params["language"] = "french"
        
        # Extract object name (for recolor/mask/count)
        if action in ["recolor", "mask", "count"]:
            obj = self._extract_object(message, color)
            if obj:
                params["object"] = obj
        
        return params
    
    def _find_color(self, message: str) -> Optional[str]:
        """Find color in message"""
        match = self.color_pattern.search(message)
        if match:
            return match.group(1).lower()
        return None
    
    def _extract_object(self, message: str, color: Optional[str] = None) -> Optional[str]:
        """Extract object name from message"""
        words = message.lower().split()
        
        # Filter out stop words, colors, and action words
        candidates = []
        for word in words:
            # Clean punctuation
            word = word.strip(".,!?;:")
            
            # Skip if stop word or color or too short
            if word in self.STOP_WORDS or word in self.COLORS or len(word) < 2:
                continue
            
            candidates.append(word)
        
        # Return first candidate (usually the object)
        if candidates:
            return candidates[0]
        
        return None
    
    def _get_missing_params(self, action: Optional[str], params: Dict) -> List[str]:
        """Determine what parameters are missing"""
        if not action:
            return []
        
        missing = []
        
        if action == "recolor":
            if "object" not in params:
                missing.append("object")
            if "color" not in params:
                missing.append("color")
        elif action == "mask":
            if "object" not in params:
                missing.append("object")
        elif action == "caption":
            # Language is optional, has default
            pass
        
        return missing
    
    def _calculate_confidence(self, action: Optional[str], params: Dict, 
                            action_confidence: float) -> float:
        """Calculate overall confidence in parse"""
        if not action:
            return 0.0
        
        # Start with action confidence
        confidence = action_confidence
        
        # Boost if we have all required params
        if action == "recolor":
            if "object" in params and "color" in params:
                confidence = min(1.0, confidence + 0.05)
        elif action == "mask":
            if "object" in params:
                confidence = min(1.0, confidence + 0.05)
        
        return confidence
    
    def needs_gemini_fallback(self, intent: Intent, message: str) -> bool:
        """Determine if we need Gemini to understand this"""
        
        # User explicitly asks for better understanding - ACTUAL USER REQUEST: only if they say "you don't understand"
        # We'll allow slight variations but disable automatic fallback.
        help_phrases = [
            "you don't understand", "u don't understand", "dont understand",
            "gemini help", "ask gemini"
        ]
        
        if any(phrase in message.lower() for phrase in help_phrases):
            return True
        
        # Automatic fallback disabled per user request
        # if intent.confidence < 0.5 and len(message) > 10:
        #     return True
        
        return False
