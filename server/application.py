from cluster import Cluster
import os
import random
import shutil

from numpy_sorter import find_close_to_many
from embedder import Embedder, Embeddings


UNSORTED_CLASS = "unsorted"
FILE_FORMAT = ".jpg"
EMBEDDINGS_FILENAME = "embeddings.h5"
RESPONSE_LIMIT = 768


class Application():
    """
        For now assumptions:
            * we operate with images only, flat input folder structure
            * all images have unique names
        ln -s /path/to/data unsorted
    """

    def __init__(self, data_root: str) -> None:
        assert os.path.isdir(data_root)
        self.data_root = data_root
        # make sure unsorted class exists
        assert os.path.exists(os.path.join(data_root, UNSORTED_CLASS))
        self.clusters: dict[str, Cluster] = {}
        self._read_clusters()
        self.unsorted = self.clusters[UNSORTED_CLASS]
        self.embeddings: Embeddings = self._init_embeddings()

    def _init_embeddings(self) -> Embeddings:
        embeddings_path = os.path.join(self.data_root, EMBEDDINGS_FILENAME)
        if os.path.exists(embeddings_path):
            embeddings = Embedder.read_embeddings(embeddings_path)
            self._assert_embeddings(embeddings)
            return embeddings
        else:
            all_items = []
            for cluster in self.clusters.values():
                all_items.extend([os.path.join(cluster.name, item) for item in cluster.items])
            all_items = sorted(all_items)
            embeddings = Embedder.generate_embeddings(self.data_root, all_items)
            # remove cluster names from items
            names = [os.path.basename(item) for item in embeddings.names]
            assert len(names) == len(set(names)), "Items names are not unique"
            embeddings = Embeddings(names, embeddings.vectors)
            Embedder.save_embeddings(embeddings_path, embeddings)
            return embeddings

    def _assert_embeddings(self, embeddings) -> None:
        assert os.path.exists(os.path.join(self.data_root, EMBEDDINGS_FILENAME))
        known = set(embeddings.names)
        for cluster in self.clusters.values():
            for item in cluster.items:
                assert item in known, f"Item {item} from {cluster.name} is not in embeddings"

    def _read_clusters(self) -> None:
        for cluster_name in os.listdir(self.data_root):
            cluster_path = os.path.join(self.data_root, cluster_name)
            if os.path.isdir(cluster_path):
                cluster = Cluster(cluster_name, cluster_path)
                self._load_cluster_items(cluster)
                self.clusters[cluster_name] = cluster

    def _load_cluster_items(self, cluster: Cluster) -> None:
        for item in os.listdir(cluster.path):
            item_path = os.path.join(cluster.path, item)
            if os.path.isfile(item_path) and item.endswith(FILE_FORMAT):
                cluster.items.add(item)
        if len(cluster.items) > 0:
            cluster.preview = cluster.items.pop()
            cluster.items.add(cluster.preview)

    def get_cluster_items(self, cluster_name: str) -> list[str]:
        assert cluster_name in self.clusters
        l = list(self.clusters[cluster_name].items)
        random.shuffle(l)
        return l[:RESPONSE_LIMIT]

    def unsorted2cluster(self, items: list[str], cluster_name: str) -> None:
        assert cluster_name in self.clusters
        self._move2cluster(self.unsorted, self.clusters[cluster_name], items)

    def create_cluster(self, cluster_name: str) -> None:
        assert cluster_name not in self.clusters
        cluster_path = os.path.join(self.data_root, cluster_name)
        os.mkdir(cluster_path)
        self.clusters[cluster_name] = Cluster(cluster_name, cluster_path)

    def sort(self, items: set[str]) -> list[str]:
        result = find_close_to_many(items, self.embeddings, RESPONSE_LIMIT)
        result = [r[0] for r in result]
        filtered = []
        for item in result:
            if item in self.unsorted.items:
                filtered.append(item)
        return filtered
    
    def sort_by_class(self, cluster_name: str) -> list[str]:
        assert cluster_name in self.clusters
        cluster = self.clusters[cluster_name]
        return self.sort(cluster.items)

    def _move2cluster(self, from_cluster: Cluster, to_cluster: Cluster, items: list[str]) -> None:
        assert len(items) > 0
        assert from_cluster.name != to_cluster.name

        for item in items:
            from_cluster.items.remove(item)
            to_cluster.items.add(item)
            from_path = os.path.join(from_cluster.path, item)
            to_path = os.path.join(to_cluster.path, item)
            shutil.move(from_path, to_path)

        # update previews if needed
        if from_cluster.preview in items:
            if len(from_cluster.items) > 0:
                from_cluster.preview = from_cluster.items.pop()
                from_cluster.items.add(from_cluster.preview)
            else:
                from_cluster.preview = None
        if to_cluster.preview is None:
            to_cluster.preview = to_cluster.items.pop()
            to_cluster.items.add(to_cluster.preview)
