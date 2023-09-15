import numpy as np
from embedder import Embeddings


def find_close_to_many(
    request: set[str],
    embeddings: Embeddings,
    target_count: int
) -> list[tuple[str, float]]:
    indices = [embeddings.names.index(name) for name in request]
    vectors = embeddings.vectors
    query = vectors[indices]
    scores = np.dot(vectors, query.T)
    scores[indices] = -np.inf
    top_score = np.max(scores, axis=1)
    top_items = np.argsort(top_score)[-target_count:][::-1]
    return [(embeddings.names[i], top_score[i]) for i in top_items]
