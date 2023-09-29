from typing import Any
import torch
import torch.nn as nn
from torch.nn import functional as F
from torch.optim.lr_scheduler import ReduceLROnPlateau, StepLR
from torchvision import models
import torchmetrics as tm
import lightning as L
import unicom


class MobileEmbeddingNet(nn.Module):
    def __init__(
        self,
        pretrained: bool,
        embedding_size=768,
    ):
        super().__init__()
        weights = None
        if pretrained:
            weights = models.MobileNet_V2_Weights.IMAGENET1K_V1
        self.backbone = models.mobilenet_v2(weights=weights)
        adapter = nn.Linear(self.backbone.last_channel, embedding_size)
        self.backbone.classifier = adapter

    def forward(self, x):
        return self.backbone(x)


losses = {
    'l1': nn.L1Loss(),
    'l2': nn.MSELoss(),
    'cosine': nn.CosineSimilarity(),
}


class EmbeddingModule(L.LightningModule):
    def __init__(
        self,
        loss: str,
        normalize: bool,
        lr: float,
        weight_decay: float,
        lr_scheduler: str | None,
        pretrained: bool,
    ) -> None:
        super().__init__()
        self.save_hyperparameters()
        assert loss in losses, f'Unknown loss {loss}'
        self.loss_function = losses[loss]
        self.normalize = normalize
        self.lr = lr
        self.weight_decay = weight_decay
        self.lr_scheduler = lr_scheduler
        self.student_model = MobileEmbeddingNet(pretrained=pretrained)

        teacher_model, _ = unicom.load("ViT-B/16")
        teacher_model.eval()
        teacher_model.requires_grad_(False) 
        # hack to prevent lightning from calling .train() and saving in checkpoints
        self.teacher_model = [teacher_model]

    def on_fit_start(self) -> None:
        self.teacher_model[0].to(self.device)

    def forward(self, x):
        return self.student_model(x)

    def configure_optimizers(self):
        optim = torch.optim.Adam(
            self.student_model.parameters(), 
            lr=self.lr,
            weight_decay=self.weight_decay,
        )
        config = {"optimizer": optim }
        if self.lr_scheduler == 'plateau':
            config['lr_scheduler'] = {
                'scheduler': ReduceLROnPlateau(optim, patience=2),
                'monitor': "val_loss",
            }
        elif self.lr_scheduler == 'step':
            config['lr_scheduler'] = {
                'scheduler': StepLR(optim, step_size=4, gamma=0.85)
            }
        else:
            assert self.lr_scheduler is None, f'Unknown lr_scheduler {self.lr_scheduler}'
        return config

    def training_step(self, x, batch_idx):
        student_embeddings = self(x)
        with torch.no_grad():
            teacher_embeddings = self.teacher_model[0](x)

        if self.normalize:
            student_embeddings = F.normalize(student_embeddings, p=2, dim=1)
            teacher_embeddings = F.normalize(teacher_embeddings, p=2, dim=1)

        loss = self.loss_function(student_embeddings, teacher_embeddings)
        self.log('train_loss', loss, prog_bar=True)
        return loss
    
    def validation_step(self, x, batch_idx):
        student_embeddings = self(x)
        with torch.no_grad():
            teacher_embeddings = self.teacher_model[0](x)
        loss_full = self.loss_function(student_embeddings, teacher_embeddings)

        student_embeddings = F.normalize(student_embeddings, p=2, dim=1)
        teacher_embeddings = F.normalize(teacher_embeddings, p=2, dim=1)
        loss_norm = self.loss_function(student_embeddings, teacher_embeddings)

        self.log('val_loss_full', loss_full, prog_bar=True)
        self.log('val_loss', loss_norm, prog_bar=True)
        return loss_full
