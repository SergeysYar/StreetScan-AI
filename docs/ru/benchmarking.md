# Бенчмаркинг

## Назначение
Подсистема бенчмаркинга сравнивает конфигурации предобработки, кластеризации и сегментации на одинаковых LiDAR-данных с воспроизводимой фиксацией метрик.

## Поддерживаемые режимы
- `preprocessing`
- `clustering`
- `segmentation`

## Входные данные
- Обязательные: файл облака точек или директория (`.ply`, `.pcd`, `.xyz`)
- Опциональные: CSV семантической ground-truth разметки (`--ground-truth-labels`)

## Конфигурация
`configs/benchmark.yaml` задает:
- выбранные режимы
- warmup и число измеряемых повторов
- наборы экспериментов для preprocessing/clustering/segmentation
- random seed и пути вывода

## Выходные файлы
- `outputs/benchmarks/benchmark_results.csv`
- `outputs/benchmarks/benchmark_summary.json`
- `outputs/reports/benchmark/benchmark_report.md`
- `outputs/plots/benchmarks/runtime_comparison.png`
- `outputs/plots/benchmarks/points_per_second.png`
- `outputs/plots/benchmarks/point_count_reduction.png`
- `outputs/plots/benchmarks/cluster_quality.png`
- `outputs/plots/benchmarks/segmentation_accuracy.png`
- `outputs/benchmarks/runs/<run_id>/run_metadata.json`
- `outputs/benchmarks/runs/<run_id>/metrics.json`

## Пояснение метрик
- Runtime агрегируется по повторам (`mean/std/min/max`).
- Пропускная способность считается в points per second.
- Качество кластеризации оценивается по статистике кластеров.
- Accuracy сегментации считается только при наличии корректной GT-разметки.

## Примеры CLI
```bash
uv run src/benchmark/benchmark_runner.py \
  --input data/raw/sample.ply \
  --output-dir outputs/benchmarks \
  --config configs/benchmark.yaml \
  --modes preprocessing clustering segmentation \
  --repetitions 3
```

```bash
uv run src/cli.py benchmark \
  --input data/raw/sample.ply \
  --output-dir outputs/benchmarks \
  --modes preprocessing clustering \
  --repetitions 3
```

## Ограничения
- Метрики accuracy недоступны при отсутствии GT или несоответствии размеров разметки.
- Ошибки отдельных экспериментов фиксируются в CSV/отчете и не прерывают остальные запуски.

