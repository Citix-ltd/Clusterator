import fire
import torch
torch.set_float32_matmul_precision('medium') # make lightning happy
import os
import lightning as L
import lightning.pytorch as pl
from lightning.pytorch.tuner import Tuner
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint, LearningRateMonitor
import clearml

from module import EmbeddingModule
from datasource import ImagesDataModule


def train(
    dataset_root: str = 'data/',  
    
    name: str|None = None,

    loss: str = "l2",
    normalize: bool = False,

    lr: float = 1e-3, 
    weight_decay: float = 1e-5,
    lr_scheduler: str = "step",
    pretrained: bool = True,

    batch_size: int = 96,
    max_epochs: int = 64,
    seed: int = 7744,
) -> None:
    if name is not None:
        clearml_task = clearml.Task.init(project_name="embeddings_kd", task_name=name)
    
    pl.seed_everything(seed)
    model = EmbeddingModule(
        loss=loss,
        normalize=normalize,
        lr = lr,
        weight_decay = weight_decay,
        lr_scheduler=lr_scheduler,
        pretrained=pretrained,
    )
    datamodule = ImagesDataModule(
        train_csv=os.path.join(dataset_root, "train.csv"),
        val_csv=os.path.join(dataset_root, "test.csv"),
        batch_size=batch_size,
        num_workers=max(4, os.cpu_count() // 2),
    )

    stoping_cb = EarlyStopping(monitor="val_loss", patience=24, mode="min")
    checkpoint_cb = ModelCheckpoint(
        monitor='val_loss',
        filename='ME-{epoch:02d}-{val_loss:.5f}',
        save_top_k=3,
        mode='min',
    )
    trainer = L.Trainer(
        max_epochs=max_epochs,
        precision=32, benchmark=True,
        callbacks=[
            stoping_cb, 
            checkpoint_cb,
            LearningRateMonitor(logging_interval='step'),
        ],
        val_check_interval=0.1,
    )
    trainer.fit(model, datamodule=datamodule)


if __name__ == "__main__":
    fire.Fire(train)
