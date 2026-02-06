from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image
import io
import uvicorn
from model_utils import generate_raw_caption, load_model
from gemini_utils import rewrite_caption_french_cloud

app = FastAPI(title="Image Captioning Backend")

@app.on_event("startup")
async def startup_event():
    # Pre-load model to avoid latency on first request
    # Note: This might be slow and consume a lot of memory.
    try:
        load_model()
    except Exception as e:
        print(f"Error loading model on startup: {e}")

@app.get("/")
def read_root():
    return {"message": "Image Captioning API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "captioning"}


@app.post("/caption")
async def caption_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")
        
        # 1. Generate Raw Caption (English)
        raw_caption = generate_raw_caption(image)
        
        # 2. Rewrite/Translate with Gemini (French)
        final_caption = rewrite_caption_french_cloud(raw_caption)
        
        return {
            "filename": file.filename,
            "raw_caption": raw_caption,
            "final_caption": final_caption
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

