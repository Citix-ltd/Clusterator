import numpy as np
import os
import h5py


def generate_embeddings(images_dir: str) -> tuple[list[str], np.ndarray]:
    import unicom
    import torch
    from torch.utils.data import DataLoader, Dataset
    from torch.nn.functional import normalize
    from tqdm import tqdm
    from PIL import Image

    class SimpleFolderDataset(Dataset):
        def __init__(self, root, transform=None):
            self.root = root
            self.transform = transform
            self.images = sorted(os.listdir(root))

        def __getitem__(self, idx):
            image = Image.open(os.path.join(self.root, self.images[idx]))
            if self.transform is not None:
                image = self.transform(image)
            return image, self.images[idx]

        def __len__(self):
            return len(self.images)

    @torch.no_grad()
    def get_features(dataset, model):
        all_features = []
        for images, _ in tqdm(DataLoader(dataset, batch_size=256, num_workers=24)):
            features = model(images.cuda())
            all_features.append(features)
        return torch.cat(all_features)

    model, preprocess = unicom.load("ViT-B/16")
    model = model.cuda()
    testset = SimpleFolderDataset(images_dir, transform=preprocess)

    torch_embedding = get_features(testset, model)
    torch_embedding = normalize(torch_embedding)
    embeddings = torch_embedding.cpu().numpy()
    return testset.images, embeddings


def save_embeddings(filename: str, data: tuple[list[str], np.ndarray]) -> None:
    with h5py.File(filename, 'w') as f:
        for k, v in zip(data[0], data[1]):
            f.create_dataset(k, data=v)


def read_embeddings(filename: str) -> tuple[list[str], np.ndarray]:
    with h5py.File(filename, 'r') as f:
        keys = list(f.keys())
        values = [f[k][()] for k in keys]
    return keys, np.array(values)


def find_close(name: str, embeddings: tuple[list[str], np.ndarray]) -> list[tuple[str, float]]:
    """
    finds the top_k closest images to the given name
    returns a list of tuples (name, score), sorted by score
    """
    names, embeddings = embeddings
    idx = names.index(name)
    scores = np.dot(embeddings, embeddings[idx])
    result = [(names[i], scores[i]) for i in range(len(names)) if i != idx]
    sort = sorted(result, key=lambda x: x[1], reverse=True)
    return sort


def merge_close(candidates: list[list[tuple[str, float]]]) -> list[tuple[str, float]]:
    """
    removes duplicates from the list of candidates
    returns a list of tuples (name, score), sorted by score
    """
    candidates = sum(candidates, [])
    candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
    seen = set()
    result = []
    for name, score in candidates:
        if name not in seen:
            result.append((name, score))
            seen.add(name)
    sort = sorted(result, key=lambda x: x[1], reverse=True)
    return sort


def find_close_to_many(names: list[str], embeddings: tuple[list[str], np.ndarray]) -> list[tuple[str, float]]:
    """
    finds the top_k closest images to the given list of names
    returns a list of tuples (name, score), sorted by score
    """
    candidates = [find_close(name, embeddings) for name in names]
    return merge_close(candidates)


