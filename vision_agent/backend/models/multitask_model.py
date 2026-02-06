import torch
import torch.nn as nn
import timm

class MultiTaskVisionModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model(
            "efficientnet_b3",
            pretrained=False,
            num_classes=0
        )
        feat_dim = self.backbone.num_features

        self.heads = nn.ModuleDict({
            "is_photo": nn.Linear(feat_dim, 1),
            "is_text": nn.Linear(feat_dim, 1),
            "is_art": nn.Linear(feat_dim, 1),
            "is_schema": nn.Linear(feat_dim, 1),
        })

    def forward(self, x):
        feats = self.backbone(x)
        return {k: torch.sigmoid(h(feats)) for k, h in self.heads.items()}
