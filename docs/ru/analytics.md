# Аналитика

## Назначение
Подсистема городской аналитики преобразует LiDAR-облака точек и опциональные семантические/кластерные/траекторные данные в интерпретируемые пространственные метрики.

## Входные данные
- Обязательные: облако точек (`.ply`, `.pcd`, `.xyz`)
- Опциональные:
  - CSV семантических меток
  - CSV статистики кластеров
  - CSV траекторий

## Основные расчеты
- Карта плотности на XY-сетке
- Сетка занятости и коэффициент занятости
- Сводка трафика (семантика или fallback по кластерам)
- Поток/концентрация пешеходов (с учетом траекторий)
- Приближенный радиальный профиль видимости
- Глобальная пространственная статистика сцены

## Выходные файлы
- `outputs/plots/analytics/<name>_density_heatmap.png`
- `outputs/analytics/<name>_occupancy_grid.csv`
- `outputs/plots/analytics/<name>_occupancy_map.png`
- `outputs/analytics/<name>_spatial_statistics.csv`
- `outputs/analytics/<name>_traffic_summary.csv`
- `outputs/analytics/<name>_pedestrian_flow.csv`
- `outputs/analytics/<name>_visibility.csv`
- `outputs/reports/analytics/<name>_analytics_report.md`

## Пример конфигурации
```yaml
analytics:
  grid_resolution: 0.5
  density_normalization: true
  occupancy_threshold: 1
  max_range: 80.0
  sensor_origin: [0.0, 0.0, 0.0]
  visibility_angle_step_deg: 1.0
  visibility_range_bins: 80
  save_plots: true
  plot_dpi: 150
  semantic_labels_path: null
  cluster_stats_path: null
  trajectory_path: null
```

## Примеры CLI
```bash
uv run src/analytics/analytics_pipeline.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/analytics \
  --config configs/analytics.yaml
```

```bash
uv run src/cli.py analyze \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/analytics \
  --semantic-labels outputs/semantic/sample_semantic_labels.csv \
  --cluster-stats outputs/clusters/sample_cluster_stats.csv \
  --grid-resolution 0.5 \
  --save-plots
```

## Ограничения
- Профиль видимости является приближенной радиальной оценкой, а не трассировкой лучей.
- При отсутствии опциональных меток и траекторий метрики трафика и пешеходного потока становятся эвристическими.

