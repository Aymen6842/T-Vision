import torch
from models.multitask_model import MultiTaskVisionModel
from PIL import Image
import torchvision.transforms as T

class PerceptionModule:
    def __init__(self, model_path, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = MultiTaskVisionModel().to(self.device)

        ckpt = torch.load(model_path, map_location=self.device, weights_only=False)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()
        
        # Image preprocessing transform
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    @torch.no_grad()
    def infer(self, image_input):
        """
        Infer image type probabilities
        Args:
            image_input: Can be a PIL Image, torch.Tensor, or bytes
        Returns:
            Dict with probabilities for each category
        """
        # Handle different input types
        if isinstance(image_input, Image.Image):
            image_tensor = self.transform(image_input)
        elif isinstance(image_input, bytes):
            import io
            pil_image = Image.open(io.BytesIO(image_input)).convert("RGB")
            image_tensor = self.transform(pil_image)
        elif isinstance(image_input, torch.Tensor):
            # Assume already preprocessed
            image_tensor = image_input
        else:
            raise ValueError(f"Unsupported input type: {type(image_input)}")
        
        image_tensor = image_tensor.unsqueeze(0).to(self.device)
        outputs = self.model(image_tensor)
        return {k: float(v.item()) for k, v in outputs.items()}

