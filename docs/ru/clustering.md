# Кластеризация

## Назначение
Подсистема кластеризации выделяет объектные группы в городских LiDAR-облаках точек для задач интерпретации трафика, последующего трекинга и семантической постобработки.

## Поддерживаемые методы
- `dbscan`: плотностная кластеризация Open3D.
- `euclidean`: радиусная кластеризация методом region-growing на основе ближайших соседей.

## Основные параметры
- `eps`: радиус окрестности DBSCAN.
- `min_points`: минимальное число точек для core-точки DBSCAN.
- `euclidean_tolerance`: радиус соседства для Euclidean-метода.
- `min_cluster_size`, `max_cluster_size`: фильтрация кластеров по размеру.
- `remove_noise`: исключение метки `-1` из валидной статистики.

## Пример DBSCAN
```bash
python src/clustering/dbscan_clustering.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/clusters \
  --config configs/clustering.yaml \
  --method dbscan \
  --eps 0.8 \
  --min-points 20
```

## Пример Euclidean
```bash
python src/clustering/dbscan_clustering.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/clusters \
  --method euclidean \
  --euclidean-tolerance 0.6 \
  --min-cluster-size 30
```

## Интеграция в общий CLI
```bash
python src/cli.py cluster \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/clusters \
  --method dbscan \
  --eps 0.8 \
  --min-points 20
```

## Выходные файлы
- `outputs/clusters/<name>_clusters.ply`
- `outputs/clusters/<name>_cluster_stats.csv`
- `outputs/clusters/<name>_cluster_labels.csv`
- `outputs/reports/clustering/<name>_cluster_report.md`
- `outputs/clusters/<name>_clusters.png` (опционально)

## Интерпретация статистики
- `point_count`, `centroid`: размер и положение объекта.
- `bbox_min/max`, `extent`, `bbox_volume`: пространственные габариты кластера.
- `density`: приближенная компактность (`points / bbox_volume`).
- `is_noise`: признак шумовых точек.

## Типовые стартовые значения
- Для городских сцен средней плотности:
  - DBSCAN: `eps=0.6..1.0`, `min_points=15..30`
  - Euclidean: `euclidean_tolerance=0.4..0.8`, `min_cluster_size=20..50`
