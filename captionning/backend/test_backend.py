import requests
import io
from PIL import Image

def test_caption():
    url = "http://localhost:8000/caption"
    
    # Create a small dummy image for testing
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    files = {'file': ('test.jpg', img_byte_arr, 'image/jpeg')}
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, files=files)
        print(f"Response Status: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            print(response.json())
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")
        print("Make sure the backend is running with 'uvicorn app:app --reload'")

if __name__ == "__main__":
    test_caption()
