# Трекинг

## Назначение
Подсистема трекинга восстанавливает траектории динамических объектов по последовательности детекций/центроидов.

## Формат входного CSV
Обязательные столбцы:
- `frame_id`, `x`, `y`, `z`

Опциональные столбцы:
- `timestamp`, `object_id`, `class_name`, `confidence`
- bbox-поля (`bbox_min_*`, `bbox_max_*`)

При отсутствии `timestamp` время вычисляется через `fps`.
При отсутствии класса используется `default_class_name`.

## Логика метода
- Покадровая ассоциация ближайшего соседа в XYZ.
- При наличии `scipy` может использоваться алгоритм Венгера.
- Опциональный фильтр Калмана постоянной скорости (`[x,y,z,vx,vy,vz]`).
- Отсев коротких треков по `min_track_length`.
- Опциональное сглаживание moving average.

## Оценка скорости
- По разности timestamp, если доступно.
- Иначе `dt = 1/fps`.
- Рассчитываются `vx, vy, vz, speed`.

## Выходные файлы
- `outputs/trajectories/<name>_tracked_objects.csv`
- `outputs/trajectories/<name>_trajectory_summary.csv`
- `outputs/plots/trajectories/<name>_trajectories_xy.png`
- `outputs/plots/trajectories/<name>_velocity.png`
- `outputs/trajectories/<name>_trajectory_overlay.ply` (опционально)
- `outputs/reports/tracking/<name>_tracking_report.md`

## Пример конфигурации
```yaml
tracking:
  fps: 10.0
  association_distance_threshold: 2.0
  max_missed_frames: 5
  min_track_length: 3
  enable_kalman_filter: true
  enable_smoothing: true
  smoothing_window: 5
  plot_dpi: 150
  save_overlay_cloud: true
  default_class_name: unknown
```

## Примеры CLI
```bash
python src/tracking/tracking_pipeline.py \
  --input data/trajectories/urban_detections.csv \
  --output-dir outputs/trajectories \
  --config configs/tracking.yaml
```

```bash
python src/cli.py track \
  --input data/trajectories/urban_detections.csv \
  --output-dir outputs/trajectories \
  --fps 10 \
  --association-distance 2.0 \
  --save-overlay-cloud
```

## Ограничения
- Геометрическая ассоциация может деградировать при длительных окклюзиях.
- Качество зависит от стабильности детекций и частоты кадров.
