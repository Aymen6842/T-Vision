import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_ID = "Salesforce/blip2-flan-t5-xl"

processor = None
model = None

def load_model():
    global processor, model
    print(f"Loading processor and model {MODEL_ID} on {DEVICE}...")
    processor = Blip2Processor.from_pretrained(MODEL_ID)
    
    # Using float16 for efficiency as in the notebook
    model = Blip2ForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
    ).to(DEVICE)
    
    model.eval()
    print("Model loaded successfully.")

def generate_raw_caption(image):
    if processor is None or model is None:
        load_model()
        
    inputs = processor(
        images=image,
        return_tensors="pt"
    ).to(DEVICE)
    
    # Cast to float16 if on CUDA
    if DEVICE == "cuda":
        inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=60,
            do_sample=False
        )

    return processor.decode(output[0], skip_special_tokens=True)
