# Визуализация

## Назначение
Подсистема визуализации формирует презентационные изображения и анимации из результатов StreetScanAI.

## Поддерживаемые входы
- Обязательный: облако точек (`.ply`, `.pcd`, `.xyz`)
- Опциональные:
  - CSV семантических меток
  - CSV кластерных меток
  - CSV сетки плотности
  - CSV occupancy-сетки
  - CSV траекторий

## Режимы рендера
- Скриншот облака точек
- Семантическая визуализация по классам
- Кластерная визуализация по ID
- Bird-eye density view
- Heatmap плотности / occupancy map
- Визуализация траекторий (2D)
- Опциональный turntable GIF

## Выходные файлы
- `outputs/visualizations/<name>_pointcloud.png`
- `outputs/visualizations/<name>_semantic.png`
- `outputs/visualizations/<name>_clusters.png`
- `outputs/visualizations/<name>_bird_eye.png`
- `outputs/visualizations/<name>_density_heatmap.png`
- `outputs/visualizations/<name>_trajectories.png`
- `outputs/visualizations/<name>_turntable.gif` (опционально)
- `outputs/reports/visualization/<name>_visualization_report.md`

## Пример конфигурации
```yaml
visualization:
  backend: open3d
  image_width: 1600
  image_height: 1000
  point_size: 2.0
  background_color: [1.0, 1.0, 1.0]
  camera_view: isometric
  save_animation: false
  animation_frames: 60
  animation_fps: 20
  bird_eye_resolution: 0.2
  plot_dpi: 150
  show_axes: true
```

## Примеры CLI
```bash
uv run src/visualization/visualization_pipeline.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/visualizations \
  --config configs/visualization.yaml
```

```bash
uv run src/cli.py visualize \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --semantic-labels outputs/semantic/sample_semantic_labels.csv \
  --cluster-labels outputs/clusters/sample_cluster_labels.csv \
  --trajectories outputs/trajectories/sample_tracked_objects.csv \
  --output-dir outputs/visualizations \
  --camera-view isometric \
  --save-animation
```

## Ограничения в headless-средах
- В безголовых окружениях off-screen рендер может быть недоступен для части backend’ов; пайплайн продолжает работу с предупреждениями.
- Для сборки GIF требуется `imageio`; иначе сохраняются кадры и фиксируется предупреждение.

