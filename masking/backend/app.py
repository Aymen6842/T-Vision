import io
import os
import torch
import numpy as np
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from transformers import Sam3Processor, Sam3Model
import matplotlib.colors as mcolors
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Masking Backend - SAM 3")

# Model configuration
# Note: In a production environment, you might want to load this once at startup
MODEL_ID = "./models/sam3"
MY_TOKEN = os.getenv("HF_TOKEN")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Using device: {DEVICE}")

# Global model and processor
processor = None
model = None

def load_models():
    global processor, model
    if processor is None or model is None:
        print("Loading SAM 3 models...")
        processor = Sam3Processor.from_pretrained(MODEL_ID, token=MY_TOKEN)
        model = Sam3Model.from_pretrained(MODEL_ID, token=MY_TOKEN).to(DEVICE)
        print("Models loaded and ready.")

@app.get("/")
async def root():
    return {
        "message": "Masking Backend - SAM 3",
        "version": "1.0.0",
        "endpoints": ["/health", "/recolor"]
    }

@app.on_event("startup")
async def startup_event():
    load_models()


def change_object_color_by_name(image, mask, color_name="red", alpha=0.6):
    """
    Translates a text string like 'red' into RGB and applies it to the mask area on the image.
    Adapted from mask_generation.ipynb
    """
    try:
        rgb_float = mcolors.to_rgb(color_name)
        target_rgb = [int(c * 255) for c in rgb_float]
    except ValueError:
        print(f"Color '{color_name}' not found. Defaulting to Red.")
        target_rgb = [255, 0, 0]

    img_np = np.array(image).copy()
    if torch.is_tensor(mask):
        mask = mask.cpu().numpy()
    mask = mask.astype(bool)

    # Broadcast mask to 3 channels if necessary
    for c in range(3):
        img_np[:, :, c] = np.where(
            mask,
            (img_np[:, :, c] * (1 - alpha) + target_rgb[c] * alpha).astype(np.uint8),
            img_np[:, :, c]
        )

    return Image.fromarray(img_np)

@app.post("/recolor")
async def recolor_image(
    file: UploadFile = File(...),
    target_obj: str = Form(...),
    new_color: str = Form(...)
):
    try:
        # 1. Read and open image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        print(f"Processing recolor request for object: '{target_obj}' with color: '{new_color}'")

        # 2. Run SAM 3 to get the mask
        inputs_sam = processor(images=image, text=target_obj, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            outputs_sam = model(**inputs_sam)

        # 3. Extract Mask
        # Using threshold 0.15 as requested
        results = processor.post_process_instance_segmentation(
            outputs_sam, threshold=0.15, target_sizes=[image.size[::-1]]
        )[0]

        print(f"SAM 3 results: found {len(results.get('masks', []))} masks at threshold 0.15")
        if 'scores' in results:
            print(f"Full scores found: {results['scores'].tolist()}")

        if len(results['masks']) == 0:
            print(f"Object '{target_obj}' not found (no masks returned even at 0.05).")
            raise HTTPException(status_code=404, detail=f"Object '{target_obj}' not found in image.")

        # Smarter Mask Selection
        masks = results['masks']
        scores = results['scores']
        
        best_mask = None
        best_score = -1
        
        # 1. Filter by score (remove very low confidence noise)
        valid_indices = [i for i, s in enumerate(scores) if s > 0.15]
        
        if not valid_indices:
            print("No masks above threshold 0.15. Falling back to highest score.")
            best_mask = masks[0]
            best_score = scores[0].item()
        else:
            # 2. From valid masks, pick the one with the LARGEST AREA
            # This heuristic assumes the user is asking for the main object, not a speck of dust
            max_area = -1
            best_idx = -1
            
            for idx in valid_indices:
                mask_area = masks[idx].sum()
                print(f"Mask {idx}: Score={scores[idx]:.3f}, Area={mask_area}")
                
                if mask_area > max_area:
                    max_area = mask_area
                    best_idx = idx
            
            best_mask = masks[best_idx]
            best_score = scores[best_idx].item()

        mask = best_mask
        print(f"Selected mask with score: {best_score:.3f}")

        # 4. Apply recoloring
        result_img = change_object_color_by_name(image, mask, color_name=new_color)

        # 5. Return the resulting image
        img_io = io.BytesIO()
        result_img.save(img_io, 'PNG')
        img_io.seek(0)
        
        print("Successfully recolored image.")
        return StreamingResponse(img_io, media_type="image/png")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mask")
async def generate_mask(
    file: UploadFile = File(...),
    target_obj: str = Form(...)
):
    try:
        # 1. Read and open image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        print(f"Processing mask generation for: '{target_obj}'")

        # 2. Run SAM 3
        inputs_sam = processor(images=image, text=target_obj, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            outputs_sam = model(**inputs_sam)

        # 3. Extract Mask
        results = processor.post_process_instance_segmentation(
            outputs_sam, threshold=0.15, target_sizes=[image.size[::-1]]
        )[0]

        if len(results['masks']) == 0:
            raise HTTPException(status_code=404, detail=f"Object '{target_obj}' not found.")

        # Take first mask and convert to black/white image
        mask = results['masks'][0]  # [H, W] bool array
        if torch.is_tensor(mask):
            mask = mask.cpu().numpy()
        mask = mask.astype(np.uint8) * 255
        
        mask_img = Image.fromarray(mask, mode='L')

        # Return image
        img_io = io.BytesIO()
        mask_img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return StreamingResponse(img_io, media_type="image/png")

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/count")
async def count_objects(
    file: UploadFile = File(...),
    target_obj: str = Form(...)
):
    """Count number of instances of an object"""
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        print(f"Counting objects for: '{target_obj}'")

        inputs_sam = processor(images=image, text=target_obj, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            outputs_sam = model(**inputs_sam)

        # 3. Extract Masks with higher threshold
        results = processor.post_process_instance_segmentation(
            outputs_sam, threshold=0.15, target_sizes=[image.size[::-1]]
        )[0]

        masks = results['masks']
        scores = results['scores']
        
        # 4. Filter by Area and Overlap (NMS-like)
        valid_masks = []
        image_area = image.size[0] * image.size[1]
        
        # Sort by score descending
        sorted_indices = torch.argsort(scores, descending=True)
        
        for idx in sorted_indices:
            mask = masks[idx]
            score = scores[idx].item()
            
            # Filter 1: Minimum Score
            if score < 0.15: 
                continue
                
            # Filter 2: Minimum Area (0.5% of image) -> Avoids noise
            mask_area = mask.sum().item()
            if mask_area < (image_area * 0.005):
                continue
            
            # Filter 3: Intersection over Union (IoU) with already selected masks
            is_duplicate = False
            for valid_mask in valid_masks:
                intersection = (mask & valid_mask).sum().item()
                union = (mask | valid_mask).sum().item()
                iou = intersection / union if union > 0 else 0
                
                # If high overlap, it's likely the same object detected twice
                if iou > 0.3:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                valid_masks.append(mask)

        count = len(valid_masks)
        print(f"Found {count} instances of {target_obj} after filtering (raw: {len(masks)})")
        
        return {"count": count, "object": target_obj}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "device": DEVICE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

