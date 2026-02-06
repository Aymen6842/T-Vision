from enum import Enum

class ConversationState(Enum):
    """States for multi-turn conversation flow"""
    IDLE = "idle"
    IMAGE_CLASSIFIED = "classified"
    AWAITING_CAPTION_LANG = "awaiting_caption_lang"
    AWAITING_RECOLOR_OBJECT = "awaiting_recolor_object"
    AWAITING_RECOLOR_COLOR = "awaiting_recolor_color"
    AWAITING_MASK_OBJECT = "awaiting_mask_object"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
