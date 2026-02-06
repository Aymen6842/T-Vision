# Vision AI Microservice Architecture

A microservice-based Vision AI system with an intelligent chatbot agent that automatically classifies images and routes requests to specialized AI services.

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ Gateway  │  :8000
    │  (8000)  │
    └────┬─────┘
         │
    ┌────┴────────────────────────────────┐
    │                                     │
┌───▼───────┐  ┌──────────┐  ┌─────────┐│
│  Chatbot  │  │Captioning│  │ Masking ││
│  (8003)   │  │  (8001)  │  │ (8002)  ││
└─────┬─────┘  └──────────┘  └─────────┘│
      │        ┌──────────┐              │
      └────────►   OCR    │◄─────────────┘
               │  (8004)  │
               └──────────┘
```

## 🚀 Services

| Service | Port | Purpose |
|---------|------|---------|
| **Gateway** | 8000 | Single entry point, routes all requests |
| **Captioning** | 8001 | Image description using vision models + Gemini |
| **Masking** | 8002 | Object segmentation and recoloring (SAM3) |
| **Agent Chatbot** | 8003 | Intelligent conversation agent with classification |
| **OCR** | 8004 | Text extraction from images |

## 🤖 Agent Chatbot Features

The chatbot provides an intelligent conversational interface:

1. **Image Classification**: Automatically classifies uploaded images as:
   - Photo (recommends captioning)
   - Text document (recommends OCR)
   - Schema/diagram (coming soon)
   - Artwork (coming soon)

2. **Confidence-Based Recommendations**: 
   - "I'm 97% confident this is a photo. I recommend captioning"
   - Users can override and choose different services

3. **Interactive Actions**:
   - Generate image captions (French + English)
   - Extract text via OCR
   - Mask and recolor objects in photos
   - Natural language commands: "recolor the bottle to red"

4. **Session Management**: Maintains conversation context across multiple interactions

## 📦 Installation

### Prerequisites
- Python 3.8+
- PyTorch with CUDA (optional, for GPU acceleration)
- Hugging Face account (for SAM3 model access)

### Setup

1. **Clone and navigate to project**:
```powershell
cd C:\Users\AYMEN\Desktop\AICV
```

2. **Install dependencies for each service**:

```powershell
# Gateway
cd gateway
pip install -r requirements.txt
cd ..

# Captioning
cd captionning\backend
pip install -r requirements.txt
cd ..\..

# Masking
cd masking\backend
pip install -r requirements.txt
cd ..\..

# OCR
cd ocr\backend
pip install -r requirements.txt
cd ..\..

# Agent Chatbot
cd vision_agent
pip install -r requirements.txt
cd ..
```

3. **Configure environment variables**:

Create `.env` files where needed:

```env
# masking/backend/.env
HF_TOKEN=your_huggingface_token

# captionning/backend/.env (if applicable)
GEMINI_API_KEY=your_gemini_api_key
```

## 🎮 Usage

### Starting All Services

Use the provided PowerShell script to start all services at once:

```powershell
.\start_services.ps1
```

This will open 5 separate PowerShell windows, one for each service.

### Manual Start

Alternatively, start each service manually in separate terminals:

```powershell
# Terminal 1 - Gateway
cd gateway
python gateway_app.py

# Terminal 2 - Captioning  
cd captionning\backend
python app.py

# Terminal 3 - Masking
cd masking\backend
python app.py

# Terminal 4 - Agent Chatbot
cd vision_agent\backend
python chatbot_app.py

# Terminal 5 - OCR
cd ocr\backend
python main.py
```

### Testing

Run the automated test suite:

```powershell
python test_chatbot_flow.py
```

This tests:
- Health checks for all services
- Gateway routing
- Chatbot conversation flow
- Image classification
- Caption generation
- OCR extraction
- Object recoloring

## 💬 Chatbot API Examples

### 1. Start a conversation

```python
import requests

# Start chat
response = requests.post("http://localhost:8000/api/chat/start")
session_id = response.json()["session_id"]
print(response.json()["message"])
# "Hello! I'm your Vision AI assistant. Please upload an image..."
```

### 2. Upload an image

```python
# Upload image for classification
with open("photo.jpg", "rb") as f:
    files = {"file": f}
    data = {"session_id": session_id}
    response = requests.post(
        "http://localhost:8000/api/chat/upload",
        files=files,
        data=data
    )

result = response.json()
print(result["message"])
# "I'm 97% confident this is a photo. I recommend captioning..."
print(result["probabilities"])
# {"is_photo": 0.97, "is_text": 0.02, "is_art": 0.01, "is_schema": 0.00}
```

### 3. Request an action

```python
# Accept recommendation (caption)
response = requests.post(
    "http://localhost:8000/api/chat/message",
    json={
        "session_id": session_id,
        "message": "caption"
    }
)
print(response.json()["message"])
# Caption result with French translation

# Or try OCR instead
response = requests.post(
    "http://localhost:8000/api/chat/message",
    json={"session_id": session_id, "message": "ocr"}
)

# Or recolor an object
response = requests.post(
    "http://localhost:8000/api/chat/message",
    json={
        "session_id": session_id,
        "message": "recolor the bottle to red"
    }
)
# Returns recolored image
```

## 🔌 Direct Service Access

All services are also accessible directly (not just through chatbot):

```python
# Direct captioning
with open("image.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/caption/caption",
        files={"file": f}
    )

# Direct OCR
with open("document.png", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/ocr/ocr",
        files={"file": f}
    )

# Direct masking
with open("photo.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/masking/recolor",
        files={"file": f},
        data={"target_obj": "bottle", "new_color": "blue"}
    )
```

## 🏥 Health Monitoring

Check service health:

```python
# Aggregate health check
response = requests.get("http://localhost:8000/health")
print(response.json())
# Shows status of all services

# Individual service health
requests.get("http://localhost:8001/health")  # Captioning
requests.get("http://localhost:8002/health")  # Masking
requests.get("http://localhost:8003/health")  # Chatbot
requests.get("http://localhost:8004/health")  # OCR
```

## 📁 Project Structure

```
AICV/
├── gateway/                    # API Gateway (port 8000)
│   ├── gateway_app.py
│   └── requirements.txt
├── captionning/backend/        # Captioning service (port 8001)
│   ├── app.py
│   ├── model_utils.py
│   └── gemini_utils.py
├── masking/backend/            # Masking service (port 8002)
│   ├── app.py
│   └── models/
├── ocr/backend/                # OCR service (port 8004)
│   ├── main.py
│   └── utils.py
├── vision_agent/backend/       # Agent Chatbot (port 8003)
│   ├── chatbot_app.py
│   ├── session_manager.py
│   ├── agent/
│   │   ├── perception.py       # Image classifier
│   │   ├── decision_policy.py  # Recommendation logic
│   │   └── actions.py
│   ├── services/
│   │   └── tool_executor.py    # HTTP client for services
│   └── models/
│       └── multitask_model.py  # Classification model
├── start_services.ps1          # Startup script
├── test_chatbot_flow.py        # Test suite
└── README.md
```

## 🔧 Configuration

### Service Ports

All ports are configured in the respective `main.py`/`app.py` files:
- Change in `uvicorn.run(app, host="0.0.0.0", port=XXXX)`

### Classification Thresholds

Adjust confidence thresholds in `vision_agent/backend/agent/config.py`:

```python
THRESHOLDS = {
    "photo": 0.80,   # 80% confidence for photo classification
    "text": 0.80,
    "art": 0.75,
    "schema": 0.75,
}
```

## 🚧 Future Features

The chatbot currently shows "coming soon" for:
- Schema/diagram analysis
- Artwork description

To add these features:
1. Implement the service backend
2. Update `vision_agent/backend/services/tool_executor.py`
3. Add routing in `gateway/gateway_app.py`

## 🐛 Troubleshooting

**Services won't start:**
- Check if ports are already in use
- Ensure all dependencies are installed
- Verify Python version (3.8+)

**Chatbot classification not working:**
- Ensure `best_multitask_model.pth` exists in `vision_agent/backend/`
- Check chatbot logs for model loading errors

**Masking service fails:**
- Verify Hugging Face token is set
- Check if SAM3 models are downloaded
- Ensure sufficient GPU memory (or use CPU)

## 📝 License

This project is for educational/research purposes.

## 🤝 Contributing

This is a modular microservice architecture. To add new AI services:
1. Create a new service directory with FastAPI backend
2. Add health check endpoint
3. Register in `gateway/gateway_app.py`
4. Update chatbot's `tool_executor.py` to call your service
