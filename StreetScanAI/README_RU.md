# StreetScanAI

StreetScanAI - инженерный фреймворк для анализа городских LiDAR-облаков точек, семантической интерпретации сцен и пространственной аналитики в задачах робототехники и автономных систем.

## Ключевые подсистемы
- Загрузка/сохранение облаков точек с валидацией форматов.
- Предобработка: voxel downsampling, удаление выбросов, фильтрация грунта.
- Кластеризация объектов: DBSCAN и евклидовая сегментация.
- Семантическая разметка и цветовая визуализация.
- Трекинг траекторий, оценка скоростей, экспорт CSV.
- Пространственная аналитика: плотность, occupancy, видимость.
- Бенчмаркинг: runtime, FPS, агрегированные метрики.

## Установка
```bash
pip install -r requirements.txt
```

## Примеры запуска
```bash
python -m src.cli preprocess --config configs/config.yaml --input data/raw/sample.ply
python -m src.cli cluster --config configs/config.yaml --input outputs/pointclouds/preprocessed.ply
python -m src.cli track --config configs/config.yaml --input outputs/pointclouds/preprocessed.ply
python -m src.cli benchmark --config configs/config.yaml --input outputs/pointclouds/preprocessed.ply
```

## Документация
Подробные материалы находятся в `docs/ru` и `docs/en`.

## Лицензия
MIT, см. файл `LICENSE`.
