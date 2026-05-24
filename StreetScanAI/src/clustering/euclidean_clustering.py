"""Euclidean clustering using nearest-neighbor graph and connected components."""
from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.neighbors import NearestNeighbors


def run_euclidean(points: np.ndarray, tolerance: float, min_cluster_size: int) -> np.ndarray:
    """Cluster points by Euclidean connectivity."""
    nn = NearestNeighbors(radius=tolerance)
    nn.fit(points)
    graph = nn.radius_neighbors_graph(points, mode="connectivity")
    n_comp, labels = connected_components(csgraph=csr_matrix(graph), directed=False)
    for idx in range(n_comp):
        if (labels == idx).sum() < min_cluster_size:
            labels[labels == idx] = -1
    return labels
