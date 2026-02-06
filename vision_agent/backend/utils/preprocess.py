import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2

_transform = A.Compose([
    A.Resize(224, 224),
    A.Normalize(),
    ToTensorV2()
])

def load_and_preprocess(path):
    image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return _transform(image=image)["image"]
