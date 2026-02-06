import easyocr
import cv2
import numpy as np
from PIL import Image
import io

class OCRProcessor:
    def __init__(self, languages=['en', 'fr']):
        # Initialize the reader only once
        self.reader = easyocr.Reader(languages)

    def process_image(self, image_bytes):
        # Convert bytes to numpy array (OpenCV format)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Read text
        results = self.reader.readtext(img_rgb)
        
        
        # Format results
        raw_data = []
        for bbox, text, confidence in results:
            # Calculate centroid for sorting
            # y_center = average of all y coordinates
            y_center = sum([pt[1] for pt in bbox]) / 4
            x_min = min([pt[0] for pt in bbox])
            
            raw_data.append({
                "text": text,
                "confidence": float(confidence),
                "bbox": [list(map(float, pt)) for pt in bbox],
                "_y": y_center,
                "_x": x_min
            })
            
        # Spatial Sort: Top-to-Bottom, Left-to-Right
        # 1. Sort by Y first
        raw_data.sort(key=lambda x: x["_y"])
        
        # 2. Group into lines (if Y difference is small, they are on same line)
        lines = []
        current_line = []
        last_y = -1000
        line_height_threshold = 20  # Pixel threshold for distinct lines
        
        for item in raw_data:
            if not current_line:
                current_line.append(item)
                last_y = item["_y"]
            else:
                if abs(item["_y"] - last_y) < line_height_threshold:
                    current_line.append(item)
                else:
                    # New line
                    lines.append(sorted(current_line, key=lambda x: x["_x"]))
                    current_line = [item]
                    last_y = item["_y"]
        
        if current_line:
            lines.append(sorted(current_line, key=lambda x: x["_x"]))
            
        # Flatten back to list
        sorted_data = [item for line in lines for item in line]
        
        # Remove internal sorting keys before returning
        for item in sorted_data:
            del item["_y"]
            del item["_x"]
            
        return sorted_data
