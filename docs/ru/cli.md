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
uv run src/cli.py --help
uv run src/cli.py preprocess --help
```

```bash
uv run src/cli.py preprocess --input data/raw/sample.ply --output-dir outputs/pointclouds/preprocessed
uv run src/cli.py cluster --input outputs/pointclouds/preprocessed/sample_preprocessed.ply --method dbscan
uv run src/cli.py segment --input outputs/pointclouds/preprocessed/sample_preprocessed.ply --method baseline
uv run src/cli.py analyze --input outputs/pointclouds/preprocessed/sample_preprocessed.ply --output-dir outputs/analytics
uv run src/cli.py track --input data/trajectories/urban_detections.csv --fps 10
uv run src/cli.py visualize --input outputs/pointclouds/preprocessed/sample_preprocessed.ply --camera-view isometric
uv run src/cli.py benchmark --input data/raw/sample.ply --modes preprocessing clustering --repetitions 3
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
uv run src/cli.py preprocess ...
uv run src/cli.py cluster ...
uv run src/cli.py segment ...
uv run src/cli.py analyze ...
uv run src/cli.py visualize ...
```

## Типовые ошибки
- Нет входного пути: укажите `--input` или задайте его в секции config.
- Некорректный YAML: исправьте синтаксис конфигурации.
- Отсутствуют опциональные файлы: где возможно, команда продолжит работу с предупреждением.

