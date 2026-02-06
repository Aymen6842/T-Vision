import requests
import os

def test_ocr(image_path):
    url = "http://localhost:8002/ocr"
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    with open(image_path, "rb") as f:
        # Explicitly specify filename and content type
        files = {"file": (os.path.basename(image_path), f, "image/png")}
        response = requests.post(url, files=files)
        
    if response.status_code == 200:
        data = response.json()
        print(f"OCR results for {data['filename']}:")
        for res in data['results']:
            print(f"- {res['text']} (confidence: {res['confidence']:.2f})")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # You can change this to a real image path
    test_image = r"c:\Users\AYMEN\Desktop\AICV\ocr_test.png"
    print(f"Testing OCR with image: {test_image}")
    test_ocr(test_image)
