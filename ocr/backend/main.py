from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utils import OCRProcessor
import uvicorn

app = FastAPI(title="OCR Backend Service")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OCR Processor
try:
    ocr_processor = OCRProcessor()
except Exception as e:
    print(f"Error initializing OCR: {e}")
    # We might want to handle this differently in production
    ocr_processor = None

@app.get("/")
def read_root():
    return {"message": "Welcome to the OCR Backend Service"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ocr"}


@app.post("/ocr")
async def perform_ocr(file: UploadFile = File(...)):
    if not ocr_processor:
        raise HTTPException(status_code=500, detail="OCR Processor not initialized")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        results = ocr_processor.process_image(contents)
        return {
            "filename": file.filename,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)

