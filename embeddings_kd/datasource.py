import albumentations as A
from albumentations.pytorch import ToTensorV2
import os
import pandas as pd
import cv2
from PIL import Image
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms as tvt
import lightning as L


class CsvImagesDataset(Dataset):
    """
        Read images from csv file
        csv file contains only image paths, without header

        Target embeddings are not pre-computed because after augmentation
        they need to be recomputed anyway
    """
    def __init__(
            self, 
            csv_file, 
            transform=None
        ):
        self.csv_file = csv_file
        self.transform = transform
        self.df = pd.read_csv(self.csv_file, header=None, names=["image_path"])

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        img_path = self.df.iloc[idx]["image_path"]
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if self.transform:
            img = self.transform(image=img)['image']
        return img


class ImagesDataModule(L.LightningDataModule):
    def __init__(
        self,
        train_csv: str,
        val_csv: str,
        batch_size: int,
        num_workers: int,
    ) -> None:
        super().__init__()
        self.train_csv = train_csv
        self.val_csv = val_csv
        self.batch_size = batch_size
        self.num_workers = num_workers

        # mean and std taken from unicom.vision_transformer
        mean = (0.48145466, 0.4578275, 0.40821073)
        std = (0.26862954, 0.26130258, 0.27577711)
        # image size is 224x224 because of the ViT-B/16 model
        common_transform = [
            A.LongestMaxSize(224),
            A.PadIfNeeded(224, 224, border_mode=cv2.BORDER_CONSTANT, value=0),
            A.Normalize(mean=mean, std=std),
            ToTensorV2(),
        ]
        self.train_transform = A.Compose([
            A.HorizontalFlip(),
            *common_transform
        ])
        self.val_transform = A.Compose(common_transform)

    def setup(self, stage: str = None) -> None:
        if stage == "fit" or stage is None:
            self.train_dataset = CsvImagesDataset(self.train_csv, self.train_transform)
            self.val_dataset = CsvImagesDataset(self.val_csv, self.val_transform)

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=True,
            pin_memory=True,
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_dataset, 
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False,
            pin_memory=True,
        )
