import numpy as np

from src.clustering.euclidean_clustering import run_euclidean


def test_euclidean_clustering_finds_two_clusters():
    cluster_a = np.random.randn(30, 3) * 0.05
    cluster_b = np.random.randn(30, 3) * 0.05 + np.array([5.0, 5.0, 0.0])
    points = np.vstack([cluster_a, cluster_b])
    labels = run_euclidean(points, tolerance=0.3, min_cluster_size=5)
    assert len(set(labels.tolist()) - {-1}) >= 2
