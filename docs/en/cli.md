# Unified CLI

## Purpose
`src/cli.py` is the unified command entrypoint for all StreetScanAI subsystems.

## Command List
- `preprocess`
- `cluster`
- `segment`
- `analyze`
- `track`
- `visualize`
- `benchmark`

## Config Behavior
- `--config` is optional (default: `configs/config.yaml`).
- Config section values are command defaults.
- Explicit CLI args override config values.
- Missing config file is handled with warning.

## Examples
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

## Recommended Pipeline Order
1. preprocess
2. cluster
3. segment
4. analyze
5. track (if dynamic sequence is available)
6. visualize
7. benchmark

Example sequence:
```bash
uv run src/cli.py preprocess ...
uv run src/cli.py cluster ...
uv run src/cli.py segment ...
uv run src/cli.py analyze ...
uv run src/cli.py visualize ...
```

## Common Errors
- Missing input path: provide `--input` or set it in config section.
- Invalid YAML: fix syntax in config file.
- Missing optional files: command continues with warnings where supported.

