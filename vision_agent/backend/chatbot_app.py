from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os

from session_manager import SessionManager
from conversation_state import ConversationState
from agent.perception import PerceptionModule
from agent.decision_policy import DecisionPolicy
from agent.actions import AgentAction
from services.tool_executor import ToolExecutor
from intent_parser import IntentParser, Intent
from gemini_handler import GeminiHandler

from services.tool_executor import ToolExecutor
from intent_parser import IntentParser, Intent
from gemini_handler import GeminiHandler
from database import UserManager, ChatHistoryManager

# Auth & DB
user_manager = UserManager()
chat_history = ChatHistoryManager()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the perception model
    global perception
    if os.path.exists(MODEL_PATH):
        print(f"Loading classification model from {MODEL_PATH}...")
        perception = PerceptionModule(MODEL_PATH)
        print("Model loaded successfully!")
    else:
        print(f"Warning: Model file {MODEL_PATH} not found!")

    if gemini_handler.is_available():
        print("Gemini fallback handler available ✓")
    else:
        print("Gemini not configured - fallback disabled")
    
    yield
    # Shutdown logic (if any) can go here

app = FastAPI(title="Vision AI Agent Chatbot", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-Id", "X-Action", "X-Object", "X-Color", "X-Message", "content-type"],
)
import urllib.parse

# Global instances
session_manager = SessionManager()
perception = None
policy = DecisionPolicy()
executor = ToolExecutor()
intent_parser = IntentParser()
gemini_handler = GeminiHandler()

MODEL_PATH = "best_multitask_model.pth"

@app.get("/")
async def root():
    return {
        "message": "Vision AI Agent Chatbot",
        "version": "2.0.0",
        "features": ["smart_conversations", "multi_turn_chat", "gemini_fallback"],
        "endpoints": ["/chat/start", "/chat/upload", "/chat/message", "/chat/session/{session_id}"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if perception is not None else "degraded",
        "service": "chatbot",
        "model_loaded": perception is not None,
        "gemini_available": gemini_handler.is_available()
    }

class ChatStartResponse(BaseModel):
    session_id: str
    message: str

@app.post("/chat/start", response_model=ChatStartResponse)
async def start_chat(user_id: Optional[int] = Form(None)):
    """Start a new chat session"""
    session = session_manager.create_session()
    
    # Persist if user logged in
    if user_id:
        chat_history.create_session(session.session_id, user_id)
        # Add welcome message to DB
        chat_history.add_message(session.session_id, "assistant", session.messages[0].content)
        
    return {
        "session_id": session.session_id,
        "message": session.messages[0].content
    }

# --- Auth Endpoints ---

@app.post("/auth/register")
async def register(username: str = Form(...), password: str = Form(...)):
    user_id = user_manager.create_user(username, password)
    if not user_id:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"user_id": user_id, "username": username}

@app.post("/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = user_manager.verify_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

@app.get("/chat/history/{user_id}")
async def get_history(user_id: int):
    return chat_history.get_user_sessions(user_id)

@app.delete("/chat/session/{session_id}")
async def delete_session(session_id: str):
    chat_history.delete_session(session_id)
    return {"status": "deleted"}

@app.get("/chat/session/{session_id}")
async def get_session_details(session_id: str):
    messages = chat_history.get_session_messages(session_id)
    return messages

@app.post("/chat/share/{session_id}")
async def share_session(session_id: str):
    # Simple implementation: Return a formatted text string
    messages = chat_history.get_session_messages(session_id)
    text_export = "Conversation with T-Vision AI:\n\n"
    for msg in messages:
        role = "User" if msg['role'] == "user" else "AI"
        text_export += f"{role}: {msg['content']}\n\n"
    return {"text": text_export}

@app.post("/chat/upload")
async def upload_image(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload an image and get classification + recommendations"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not perception:
        raise HTTPException(status_code=503, detail="Classification model not loaded")
    
    # Read image
    image_bytes = await file.read()
    session_manager.set_image(session_id, image_bytes, file.filename)
    
    # Classify image
    probs = perception.infer(image_bytes)
    action, confidence, reason = policy.decide(probs)
    
    # Format probabilities
    prob_text = ", ".join([f"{k.replace('is_', '')}: {v*100:.1f}%" for k, v in probs.items()])
    
    # Generate recommendation
    message_intro = f"I've received your image! 📸 (Confidence: {confidence*100:.0f}%)\n\nWhat would you like me to do with it?"
    
    if action == AgentAction.CAPTION_IMAGE:
        available = ["caption", "ocr", "recolor", "mask"]
    elif action == AgentAction.RUN_OCR:
        available = ["ocr", "caption"]
    else:
        available = ["caption", "ocr"]
    
    # Additional suggestions based on image type
    recommendation = message_intro + "\n\nYou can ask me to:\n• **Caption** it\n• **Recolor** an object\n• Create a **mask**\n• Extract **text** (OCR)"
    
    # Store in session
    session_manager.set_classification(session_id, probs, action.value, available)
    session.state = ConversationState.IMAGE_CLASSIFIED
    save_message(session_id, "assistant", recommendation)
    
    return {
        "session_id": session_id,
        "filename": file.filename,
        "probabilities": probs,
        "recommended_action": action.value,
        "confidence": confidence,
        "message": recommendation,
        "available_actions": available,
        "details": prob_text
    }

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

@app.post("/chat/message")
async def send_message(request: ChatMessageRequest):
    """Handle user messages with smart multi-turn conversations"""
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.current_image:
        return {
            "session_id": request.session_id,
            "message": "Please upload an image first! 📷",
            "action_taken": None
        }
    
    # Add user message to history
    save_message(request.session_id, "user", request.message)
    
    # Handle based on current conversation state
    if session.state in [ConversationState.AWAITING_CAPTION_LANG,
                         ConversationState.AWAITING_RECOLOR_OBJECT,
                         ConversationState.AWAITING_RECOLOR_COLOR,
                         ConversationState.AWAITING_MASK_OBJECT]:
        # Continue multi-turn flow
        return await handle_pending_action(session, request.message)
    else:
        # Parse new intent
        return await handle_new_intent(session, request.message)

async def handle_new_intent(session, message: str):
    """Handle a new user intent"""
    
    # Parse intent using rule-based parser
    intent = intent_parser.parse(message, session.state.value)
    
    # Check if we need Gemini fallback
    if intent_parser.needs_gemini_fallback(intent, message):
        return await handle_gemini_fallback(session, message, intent)
    
    # Route to appropriate handler
    # Route to appropriate handler
    if intent.action == "greeting":
        return await handle_greeting(session)
    elif intent.action == "count":
        return await handle_count_request(session, intent)
    elif intent.action == "caption":
        return await handle_caption_request(session, intent)
    elif intent.action == "ocr":
        return await handle_ocr_request(session, intent)
    elif intent.action == "recolor":
        # Smart Context Logic
        if "object" not in intent.parameters:
            if session.last_object:
                # Ask clarification
                session.pending_action = "recolor"
                session.state = ConversationState.AWAITING_RECOLOR_OBJECT
                msg = f"Do you mean the {session.last_object}? (Yes/No)"
                save_message(session.session_id, "assistant", msg)
                return {
                    "session_id": session.session_id,
                    "message": msg,
                    "action_taken": None
                }
        return await handle_recolor_request(session, intent)
    elif intent.action == "mask":
         if "object" not in intent.parameters and session.last_object:
               # Ask clarification
                session.pending_action = "mask"
                session.state = ConversationState.AWAITING_MASK_OBJECT
                msg = f"Do you mean the {session.last_object}? (Yes/No)"
                save_message(session.session_id, "assistant", msg)
                return {
                    "session_id": session.session_id,
                    "message": msg,
                    "action_taken": None
                }
         return await handle_mask_request(session, intent)
    elif intent.action == "recolor":
        return await handle_recolor_request(session, intent)
    elif intent.action == "mask":
        return await handle_mask_request(session, intent)
    else:
        # Unclear intent
        return {
            "session_id": session.session_id,
            "message": "I'm not sure what you want me to do. 🤔\n\nYou can ask me to:\n"
                      "• **Caption** the image (English or French)\n"
                      "• Extract **text** (OCR)\n"
                      "• **Recolor** an object\n"
                      "• Create a **mask** of an object",
            "action_taken": None
        }

async def handle_count_request(session, intent: Intent):
    """Handle count request"""
    obj = intent.parameters.get("object")
    
    # If no object specified, ask for it
    if not obj:
        # Check if we have a context object
        if session.last_object:
            obj = session.last_object
        else:
            msg = "What would you like me to count? 🔢"
            save_message(session.session_id, "assistant", msg)
            return {
                "session_id": session.session_id,
                "message": msg,
                "action_taken": None
            }

    # Execute count
    result = executor.count(session.current_image, obj)
    
    if "error" in result:
        msg = f"❌ {result['error']}"
    else:
        count = result.get("count", 0)
        obj_name = result.get("object", obj)
        
        if count == 0:
            msg = f"I didn't find any {obj_name}s in the image. 🤷‍♂️"
        elif count == 1:
            msg = f"I found **1** {obj_name}. 1️⃣"
        else:
            msg = f"I found **{count}** {obj_name}s! 🔢"
            
        # Update context
        session.last_object = obj_name
        
    session.state = ConversationState.IDLE
    save_message(session.session_id, "assistant", msg)
    
    return {
        "session_id": session.session_id,
        "message": msg,
        "action_taken": "count"
    }

async def handle_caption_request(session, intent: Intent):
    """Handle caption request"""
    language = intent.parameters.get("language", session.language_pref)
    
    if not intent.parameters.get("language"):
        # Ask for language preference
        session.pending_action = "caption"
        session.state = ConversationState.AWAITING_CAPTION_LANG
        session_manager.add_message(session.session_id, "assistant",
                                   "Would you like the caption in English 🇬🇧 or French 🇫🇷?")
        return {
            "session_id": session.session_id,
            "message": "Would you like the caption in English 🇬🇧 or French 🇫🇷?",
            "action_taken": None
        }
    
    # Execute caption
    result = executor.caption(session.current_image)
    
    if "error" in result:
        msg = f"❌ Sorry, something went wrong: {result['error']}"
    else:
        if language == "english":
            msg = f"✅ **Caption (English):**\n\n{result.get('raw_caption', 'N/A')}"
        else:
            msg = f"✅ **Caption (French):**\n\n{result.get('final_caption', 'N/A')}\n\n_Original: {result.get('raw_caption', 'N/A')}_"
    
    session.state = ConversationState.IDLE
    save_message(session.session_id, "assistant", msg)
    
    return {
        "session_id": session.session_id,
        "message": msg,
        "action_taken": "caption"
    }

async def handle_ocr_request(session, intent: Intent):
    """Handle OCR request"""
    result = executor.ocr(session.current_image)
    
    if "error" in result:
        msg = f"❌ {result['error']}"
    else:
        ocr_results = result.get('results', [])
        if ocr_results:
            # Join all text with newlines for a clean block
            full_text = "\n".join([item.get('text', '') for item in ocr_results])
            
            msg = f"✅ **Text Extracted** ({result.get('count', 0)} lines found):\n\n"
            msg += "```text\n"
            msg += full_text
            msg += "\n```"
        else:
            msg = "I couldn't find any text in this image. 🔍"
    
    session.state = ConversationState.IDLE
    save_message(session.session_id, "assistant", msg)
    
    return {
        "session_id": session.session_id,
        "message": msg,
        "action_taken": "ocr"
    }


async def handle_greeting(session):
    msg = "Hello! 👋 How can I help you today? I can caption images, read text (OCR), count objects, or recolor them!"
    save_message(session.session_id, "assistant", msg)
    return {
        "session_id": session.session_id,
        "message": msg,
        "action_taken": "greeting"
    }

async def handle_recolor_request(session, intent: Intent):
    """Handle recolor request"""
    obj = intent.parameters.get("object")
    color = intent.parameters.get("color")
    
    # Check what's missing
    if not obj:
        session.pending_action = "recolor"
        session.pending_params = intent.parameters
        session.state = ConversationState.AWAITING_RECOLOR_OBJECT
        msg = "What object would you like to recolor? 🎨"
        save_message(session.session_id, "assistant", msg)
        return {
            "session_id": session.session_id,
            "message": msg,
            "action_taken": None
        }
    
    if not color:
        session.pending_action = "recolor"
        session.pending_params = {"object": obj}
        session.state = ConversationState.AWAITING_RECOLOR_COLOR
        msg = f"What color for the {obj}? (e.g., red, blue, green...)"
        save_message(session.session_id, "assistant", msg)
        return {
            "session_id": session.session_id,
            "message": msg,
            "action_taken": None
        }
    
    # Execute recolor
    return await execute_recolor(session, obj, color)

async def handle_mask_request(session, intent: Intent):
    """Handle mask request"""
    obj = intent.parameters.get("object")
    
    if not obj:
        session.pending_action = "mask"
        session.state = ConversationState.AWAITING_MASK_OBJECT
        msg = "What object should I create a mask for?"
        save_message(session.session_id, "assistant", msg)
        return {
            "session_id": session.session_id,
            "message": msg,
            "action_taken": None
        }
    
    # Execute mask generation
    return await execute_mask(session, obj)

async def handle_pending_action(session, message: str):
    """Continue a multi-turn conversation"""
    
    if session.state == ConversationState.AWAITING_CAPTION_LANG:
        # User chose language
        intent = intent_parser.parse(message)
        language = intent.parameters.get("language", "english")
        session.language_pref = language
        session.state = ConversationState.IDLE
        
        # Execute caption with chosen language
        temp_intent = Intent(action="caption", parameters={"language": language}, confidence=1.0, missing_params=[])
        return await handle_caption_request(session, temp_intent)
    
    elif session.state == ConversationState.AWAITING_RECOLOR_OBJECT:
        # User provided object
        intent = intent_parser.parse(message, "recolor")
        obj = intent.parameters.get("object") or message.strip().lower()
        session.pending_params["object"] = obj
        session.state = ConversationState.AWAITING_RECOLOR_COLOR
        
        msg = f"Got it! What color for the {obj}? 🎨"
        save_message(session.session_id, "assistant", msg)
        return {
            "session_id": session.session_id,
            "message": msg,
            "action_taken": None
        }
    
    elif session.state == ConversationState.AWAITING_RECOLOR_COLOR:
        # User provided color
        intent = intent_parser.parse(message, "recolor")
        color = intent.parameters.get("color")
        
        if not color:
            # Try to extract from message
            color = message.strip().lower()
            if color not in intent_parser.COLORS:
                msg = (f"I don't recognize '{color}' as a color. 🤔\n\n"
                      f"Try: {', '.join(intent_parser.COLORS[:10])}...")
                save_message(session.session_id, "assistant", msg)
                return {
                    "session_id": session.session_id,
                    "message": msg,
                    "action_taken": None
                }
        
        obj = session.pending_params.get("object", "object")
        return await execute_recolor(session, obj, color)
    
    elif session.state == ConversationState.AWAITING_MASK_OBJECT:
        # User provided object for mask
        obj = message.strip().lower()
        return await execute_mask(session, obj)

async def execute_recolor(session, obj: str, color: str):
    """Execute recolor action"""
    result = executor.recolor(session.current_image, obj, color)
    
    if "error" in result:
        # Check if object not found
        if "not found" in result["error"].lower():
            msg = (f"I couldn't find a '{obj}' in the picture. 🔍\n\n"
                  f"Are you sure that's what you're looking for? "
                  f"Maybe try a different description?")
        else:
            msg = f"❌ Something went wrong: {result['error']}"
        
        session.state = ConversationState.IDLE
        save_message(session.session_id, "assistant", msg)
        return {
            "session_id": session.session_id,
            "message": msg,
            "action_taken": "recolor_failed"
        }
    
    elif "image" in result:
        # Success - return image
        session.state = ConversationState.IDLE
        # Update context
        session.last_object = obj
        session.last_color = color
        
        success_msg = f"✅ Recolored the {obj} to {color}!"
        save_message(session.session_id, "assistant", success_msg)
        
        return StreamingResponse(
            iter([result["image"]]),
            media_type=result["content_type"],
            headers={
                "X-Session-Id": session.session_id,
                "X-Action": "recolor",
                "X-Object": obj,
                "X-Color": color,
                "X-Message": urllib.parse.quote(success_msg)
            }
        )

async def execute_mask(session, obj: str):
    """Execute mask action"""
    result = executor.mask(session.current_image, obj)
    
    if "error" in result:
        # Check if object not found
        if "not found" in result["error"].lower():
            msg = (f"I couldn't find a '{obj}' in the picture. 🔍\n\n"
                  f"Are you sure that's what you're looking for? "
                  f"Maybe try a different description?")
        else:
            msg = f"❌ Something went wrong: {result['error']}"
        
        session.state = ConversationState.IDLE
        save_message(session.session_id, "assistant", msg)
        return {
            "session_id": session.session_id,
            "message": msg,
            "action_taken": "mask_failed"
        }
    
    elif "image" in result:
        # Success - return image
        session.state = ConversationState.IDLE
        success_msg = f"✅ Created a mask for {obj}!"
        save_message(session.session_id, "assistant", success_msg)
        
        return StreamingResponse(
            iter([result["image"]]),
            media_type=result["content_type"],
            headers={
                "X-Session-Id": session.session_id,
                "X-Action": "mask",
                "X-Object": obj,
                "X-Message": urllib.parse.quote(success_msg)
            }
        )

async def handle_gemini_fallback(session, message: str, failed_intent: Intent):
    """Use Gemini to understand unclear intents"""
    
    if not gemini_handler.is_available():
        msg = ("I'm not sure what you mean. Could you rephrase that?\n\n"
              "I can help with: captions, OCR, recoloring objects, or creating masks.")
        save_message(session.session_id, "assistant", msg)
        return {
            "session_id": session.session_id,
            "message": msg,
            "action_taken": None
        }
    
    # Ask Gemini for help
    context = {
        "has_image": session.current_image is not None,
        "image_type": session.recommended_action or "unknown"
    }
    
    gemini_result = gemini_handler.understand_intent(message, context)
    
    if not gemini_result.get("success"):
        msg = gemini_result.get("message", "I'm having trouble understanding. Could you rephrase?")
        save_message(session.session_id, "assistant", msg)
        return {
            "session_id": session.session_id,
            "message": msg,
            "action_taken": None
        }
    
    # Check if bot can do it
    if not gemini_result.get("can_bot_do_it"):
        msg = gemini_handler.generate_polite_refusal(gemini_result.get("explanation", "that"))
        save_message(session.session_id, "assistant", msg)
        return {
            "session_id": session.session_id,
            "message": msg,
            "action_taken": None
        }
    
    # Gemini understood and it's doable - create intent and execute
    action = gemini_result.get("action")
    params = gemini_result.get("parameters", {})
    new_intent = Intent(action=action, parameters=params, confidence=0.9, missing_params=[])
    
    # Add confirmation message
    confirmation = f"Ah, I understand now! {gemini_result.get('explanation')} 💡\n\n"
    save_message(session.session_id, "assistant", confirmation)
    
    # Execute the action
    if action == "caption":
        return await handle_caption_request(session, new_intent)
    elif action == "ocr":
        return await handle_ocr_request(session, new_intent)
    elif action == "recolor":
        return await handle_recolor_request(session, new_intent)
    elif action == "mask":
        return await handle_mask_request(session, new_intent)

@app.get("/chat/session/{session_id}")
async def get_session(session_id: str):
    """Get conversation history for a session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "created_at": session.created_at.isoformat(),
        "has_image": session.current_image is not None,
        "image_name": session.current_image_name,
        "classification": session.classification_results,
        "recommended_action": session.recommended_action,
        "conversation_state": session.state.value,
        "pending_action": session.pending_action,
        "language_preference": session.language_pref,
        "conversation": session_manager.get_conversation_history(session_id)
    }


def save_message(session_id: str, role: str, content: str):
    """Helper to save message to both memory and DB"""
    session_manager.add_message(session_id, role, content)
    # Only save to DB if it's a valid session that exists in DB
    # We can assume if it's in session_manager it might be in DB, 
    # but we should catch errors or just fire and forget
    try:
        chat_history.add_message(session_id, role, content)
    except Exception as e:
        print(f"Warning: Could not save message to DB: {e}")

if __name__ == "__main__":
    print("Starting Enhanced Vision AI Agent Chatbot on port 8003...")
    print("Features: Smart conversations, Multi-turn flows, Gemini fallback")
    uvicorn.run(app, host="0.0.0.0", port=8003)
