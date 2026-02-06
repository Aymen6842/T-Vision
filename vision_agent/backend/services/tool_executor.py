from agent.actions import AgentAction
import httpx
import io
from PIL import Image

class ToolExecutor:
    def __init__(self):
        self.service_urls = {
            "captioning": "http://localhost:8001",
            "ocr": "http://localhost:8004",
            "masking": "http://localhost:8002"
        }
    
    def execute(self, action: AgentAction, image_input):
        if action == AgentAction.CAPTION_IMAGE:
            return self.caption(image_input)

        if action == AgentAction.RUN_OCR:
            return self.ocr(image_input)

        if action == AgentAction.ANALYZE_SCHEMA:
            return self.schema(image_input)

        if action == AgentAction.ART_DESCRIPTION:
            return self.art(image_input)

        return {"error": "No suitable action"}
    
    def _image_to_bytes(self, image_input):
        """Convert image input to bytes for HTTP upload"""
        if isinstance(image_input, bytes):
            return image_input
        elif isinstance(image_input, Image.Image):
            buf = io.BytesIO()
            image_input.save(buf, format='PNG')
            return buf.getvalue()
        else:
            raise ValueError(f"Unsupported image type: {type(image_input)}")

    def caption(self, image_input):
        """Call captioning microservice"""
        try:
            image_bytes = self._image_to_bytes(image_input)
            
            with httpx.Client(timeout=30.0) as client:
                files = {"file": ("image.png", image_bytes, "image/png")}
                response = client.post(f"{self.service_urls['captioning']}/caption", files=files)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Captioning service error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to call captioning service: {str(e)}"}

    def ocr(self, image_input):
        """Call OCR microservice"""
        try:
            image_bytes = self._image_to_bytes(image_input)
            
            with httpx.Client(timeout=30.0) as client:
                files = {"file": ("image.png", image_bytes, "image/png")}
                response = client.post(f"{self.service_urls['ocr']}/ocr", files=files)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"OCR service error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to call OCR service: {str(e)}"}
    
    def recolor(self, image_input, target_obj: str, new_color: str):
        """Call masking service to recolor an object"""
        try:
            image_bytes = self._image_to_bytes(image_input)
            
            with httpx.Client(timeout=60.0) as client:
                files = {"file": ("image.png", image_bytes, "image/png")}
                data = {"target_obj": target_obj, "new_color": new_color}
                response = client.post(
                    f"{self.service_urls['masking']}/recolor",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    # Return image bytes
                    return {"image": response.content, "content_type": response.headers.get("content-type")}
                elif response.status_code == 404:
                    return {"error": f"Object '{target_obj}' not found in the image"}
                else:
                    return {"error": f"Masking service error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to call masking service: {str(e)}"}
            
    def mask(self, image_input, target_obj: str):
        """Call masking service to generate a mask for an object"""
        try:
            image_bytes = self._image_to_bytes(image_input)
            
            with httpx.Client(timeout=60.0) as client:
                files = {"file": ("image.png", image_bytes, "image/png")}
                data = {"target_obj": target_obj}
                response = client.post(
                    f"{self.service_urls['masking']}/mask",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    return {"image": response.content, "content_type": response.headers.get("content-type")}
                elif response.status_code == 404:
                    return {"error": f"Object '{target_obj}' not found"}
                else:
                    return {"error": f"Masking service error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to call masking service: {str(e)}"}

    def count(self, image_input, target_obj: str):
        """Call masking service to count objects"""
        try:
            image_bytes = self._image_to_bytes(image_input)
            
            with httpx.Client(timeout=60.0) as client:
                files = {"file": ("image.png", image_bytes, "image/png")}
                data = {"target_obj": target_obj}
                response = client.post(
                    f"{self.service_urls['masking']}/count",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Masking service error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to call masking service: {str(e)}"}

    def schema(self, image_input):
        """Schema analysis - coming soon"""
        return {
            "message": "Schema analysis is coming soon! This feature is under development.",
            "status": "not_implemented"
        }

    def art(self, image_input):
        """Art description - coming soon"""
        return {
            "message": "Art description is coming soon! This feature is under development.",
            "status": "not_implemented"
        }

