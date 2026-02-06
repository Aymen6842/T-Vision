from enum import Enum

class AgentAction(Enum):
    CAPTION_IMAGE = "caption_image"
    RUN_OCR = "run_ocr"
    ANALYZE_SCHEMA = "analyze_schema"
    ART_DESCRIPTION = "art_description"
    REJECT = "reject"
