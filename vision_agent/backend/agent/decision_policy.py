from agent.actions import AgentAction
from agent.config import THRESHOLDS

class DecisionPolicy:
    def decide(self, probs: dict):
        if probs["is_text"] >= THRESHOLDS["text"]:
            return AgentAction.RUN_OCR, probs["is_text"], "Text-dominant image"

        if probs["is_schema"] >= THRESHOLDS["schema"]:
            return AgentAction.ANALYZE_SCHEMA, probs["is_schema"], "Technical schematic"

        if probs["is_art"] >= THRESHOLDS["art"]:
            return AgentAction.ART_DESCRIPTION, probs["is_art"], "Artistic image"

        if probs["is_photo"] >= THRESHOLDS["photo"]:
            return AgentAction.CAPTION_IMAGE, probs["is_photo"], "Real-world photo"

        return AgentAction.REJECT, max(probs.values()), "Low confidence"
