import numpy as np
import os
import h5py
from dataclasses import dataclass
from typing import TypeAlias
import torch
from torch.utils.data import DataLoader, Dataset
from torch.nn.functional import normalize
from tqdm import tqdm
from PIL import Image
import unicom


@dataclass(frozen=True)
class Embeddings:
    names: list[str]
    vectors: np.ndarray


class _SimpleImagesListDataset(Dataset):
    def __init__(self, data_root:str, images: list[str], transform=None):
        self.data_root = data_root
        self.images = images
        self.transform = transform

    def __getitem__(self, idx):
        image_name = self.images[idx]
        image = Image.open(os.path.join(self.data_root, image_name))
        if self.transform is not None:
            image = self.transform(image)
        return image, image_name

    def __len__(self):
        return len(self.images)


class Embedder():
    batch_size: int = 256
    num_workers: int = 12
    device: str = 'cuda:0'

    def generate_embeddings(data_root: str, images: list[str]) -> Embeddings:
        model, preprocess = unicom.load("ViT-B/16")
        model = model.to(Embedder.device)
        dataset = _SimpleImagesListDataset(data_root, images, transform=preprocess)

        with torch.no_grad():
            all_features = []
            dataloader = DataLoader(dataset, batch_size=Embedder.batch_size, num_workers=Embedder.num_workers)
            for data, _ in tqdm(dataloader):
                features = model(data.to(Embedder.device))
                all_features.append(features)
            torch_embedding = torch.cat(all_features)
            torch_embedding = normalize(torch_embedding)
            embeddings = torch_embedding.cpu().numpy()
        return Embeddings(images, embeddings)

    @staticmethod
    def save_embeddings(path: str, data: Embeddings) -> None:
        with h5py.File(path, 'w') as f:
            for k, v in zip(data.names, data.vectors):
                f.create_dataset(k, data=v)

    @staticmethod
    def read_embeddings(path: str) -> Embeddings:
        assert os.path.exists(path), f"File {path} does not exist"
        with h5py.File(path, 'r') as f:
            keys = list(f.keys())
            values = [f[k][()] for k in keys]
        return Embeddings(keys, np.array(values))
