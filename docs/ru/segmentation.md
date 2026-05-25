# Сегментация

## Назначение
Подсистема семантической сегментации выполняет покомпонентную разметку точек городского LiDAR-облака для последующих этапов восприятия и аналитики.

## Поддерживаемые классы
- `0 unlabeled`
- `1 road`
- `2 building`
- `3 vehicle`
- `4 pedestrian`
- `5 vegetation`
- `6 pole`
- `7 traffic_sign`

## Базовый метод
Режим `baseline` реализован как детерминированный набор правил:
- нормализация высоты относительно минимального `Z`
- присвоение `road` для околоземных точек
- диапазонные правила по высоте для `vehicle` и `pedestrian`
- разделение высоких структур на `building`/`vegetation` по локальной плотности
- выделение узких вертикальных структур как `pole`/`traffic_sign`

Это интерпретируемый базовый подход, а не обученная нейросетевая модель.

## Заглушка PointNet++
Режим `pointnet` является контрактом интеграции. При отсутствии весов выполнение завершается явной ошибкой.
Фиктивные предсказания не генерируются.

## Вход / Выход
- Вход: `.ply`, `.pcd`, `.xyz`
- Выход:
  - `outputs/semantic/<name>_semantic.ply`
  - `outputs/semantic/<name>_semantic_labels.csv`
  - `outputs/semantic/<name>_semantic_stats.csv`
  - `outputs/reports/segmentation/<name>_segmentation_report.md`
  - опционально `outputs/semantic/<name>_semantic.png`

## Пример конфигурации
```yaml
segmentation:
  method: baseline
  weights_path: null
  device: cpu
  use_cluster_features: false
  cluster_labels_path: null
  cluster_stats_path: null
  z_ground_threshold: 0.25
  z_vehicle_min: 0.3
  z_vehicle_max: 2.2
  z_pedestrian_min: 0.5
  z_pedestrian_max: 2.5
  pole_radius_threshold: 0.25
  min_points_per_object: 20
  save_screenshot: false
  output_format: ply
```

## Примеры CLI
```bash
python src/segmentation/semantic_segmentation.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/semantic \
  --method baseline
```

```bash
python src/cli.py segment \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/semantic \
  --method baseline \
  --config configs/segmentation.yaml
```

## Ограничения и развитие
- Качество baseline-правил зависит от типа сцены.
- Для режима PointNet++ требуется реальная интеграция обученной модели.
