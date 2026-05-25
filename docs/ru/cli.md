# Единый CLI

## Назначение
`src/cli.py` — единая точка запуска подсистем StreetScanAI.

## Список команд
- `preprocess`
- `cluster`
- `segment`
- `analyze`
- `track`
- `visualize`
- `benchmark`

## Поведение конфигурации
- `--config` опционален (по умолчанию `configs/config.yaml`).
- Значения из секции команды используются как defaults.
- Явно переданные CLI-аргументы имеют приоритет.
- При отсутствии config выводится предупреждение.

## Примеры
```bash
python src/cli.py --help
python src/cli.py preprocess --help
```

```bash
python src/cli.py preprocess --input data/raw/sample.ply --output-dir outputs/pointclouds/preprocessed
python src/cli.py cluster --input outputs/pointclouds/preprocessed/sample_preprocessed.ply --method dbscan
python src/cli.py segment --input outputs/pointclouds/preprocessed/sample_preprocessed.ply --method baseline
python src/cli.py analyze --input outputs/pointclouds/preprocessed/sample_preprocessed.ply --output-dir outputs/analytics
python src/cli.py track --input data/trajectories/urban_detections.csv --fps 10
python src/cli.py visualize --input outputs/pointclouds/preprocessed/sample_preprocessed.ply --camera-view isometric
python src/cli.py benchmark --input data/raw/sample.ply --modes preprocessing clustering --repetitions 3
```

## Рекомендуемый порядок пайплайна
1. preprocess
2. cluster
3. segment
4. analyze
5. track (если есть динамическая последовательность)
6. visualize
7. benchmark

Пример последовательности:
```bash
python src/cli.py preprocess ...
python src/cli.py cluster ...
python src/cli.py segment ...
python src/cli.py analyze ...
python src/cli.py visualize ...
```

## Типовые ошибки
- Нет входного пути: укажите `--input` или задайте его в секции config.
- Некорректный YAML: исправьте синтаксис конфигурации.
- Отсутствуют опциональные файлы: где возможно, команда продолжит работу с предупреждением.
