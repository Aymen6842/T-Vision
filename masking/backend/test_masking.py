import requests

def test_recolor():
    url = "http://127.0.0.1:8001/recolor"
    image_path = "test_bottle.jpg"
    
    data = {
        "target_obj": "bottle",
        "new_color": "blue"
    }
    
    with open(image_path, "rb") as f:
        files = {"file": f}
        print(f"Sending request to {url}...")
        response = requests.post(url, data=data, files=files)
        
    if response.status_code == 200:
        with open("recolored_bottle.jpg", "wb") as f:
            f.write(response.content)
        print("Success! Recolored image saved as 'recolored_bottle.jpg'")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_recolor()
