import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from conversation_state import ConversationState

@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationSession:
    session_id: str
    messages: List[Message] = field(default_factory=list)
    current_image: Optional[bytes] = None
    current_image_name: Optional[str] = None
    classification_results: Optional[Dict] = None
    recommended_action: Optional[str] = None
    available_actions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Enhanced conversation state
    state: ConversationState = ConversationState.IDLE
    pending_action: Optional[str] = None
    pending_params: Dict[str, Any] = field(default_factory=dict)
    language_pref: str = "english"
    language_pref: str = "english"
    last_error: Optional[str] = None
    
    # Context Memory
    last_object: Optional[str] = None
    last_color: Optional[str] = None

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
    
    def create_session(self) -> ConversationSession:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        session = ConversationSession(session_id=session_id)
        self.sessions[session_id] = session
        
        # Add welcome message
        welcome_msg = Message(
            role="assistant",
            content="Hello! I'm your Vision AI assistant. Please upload an image to get started. I'll analyze it and recommend the best action for you!"
        )
        session.messages.append(welcome_msg)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get an existing session"""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the conversation history"""
        session = self.get_session(session_id)
        if session:
            session.messages.append(Message(role=role, content=content))
    
    def set_image(self, session_id: str, image_bytes: bytes, filename: str):
        """Store uploaded image in session"""
        session = self.get_session(session_id)
        if session:
            session.current_image = image_bytes
            session.current_image_name = filename
    
    def set_classification(self, session_id: str, results: Dict, recommended_action: str, available_actions: List[str]):
        """Store classification results"""
        session = self.get_session(session_id)
        if session:
            session.classification_results = results
            session.recommended_action = recommended_action
            session.available_actions = available_actions
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get formatted conversation history"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages
        ]
