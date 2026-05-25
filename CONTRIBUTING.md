# Contributing to StreetScanAI

## Project Overview
StreetScanAI is a modular LiDAR perception and urban spatial analytics framework. Contributions should preserve reproducibility, modularity, and production-grade engineering quality.

## Repository Structure
- `src/`: subsystem implementations (`preprocessing`, `clustering`, `segmentation`, `analytics`, `tracking`, `visualization`, `benchmark`)
- `configs/`: YAML runtime configurations
- `docs/`: English and Russian technical docs
- `tests/`: baseline unit tests
- `outputs/`: generated artifacts (kept via `.gitkeep`)

## Setup
```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Development Workflow
1. Create a branch from `main`.
2. Implement focused, reviewable changes.
3. Run local checks/tests.
4. Update docs/config examples if behavior changed.
5. Open PR with clear scope and validation notes.

## Code Style
- Python 3.10+
- Type hints and docstrings required
- `pathlib.Path` for filesystem paths
- No hardcoded absolute OS-specific paths
- Keep algorithm logic inside subsystem modules (not CLI)

## Commit Convention
Use imperative, subsystem-oriented commit messages.
Examples:
- `feat(tracking): add Kalman-based trajectory association`
- `docs(cli): polish command examples and config behavior`
- `fix(benchmark): handle missing ground-truth labels gracefully`

## Branch Naming Examples
- `feature/preprocessing-ground-filter-tuning`
- `fix/cli-config-override`
- `docs/readme-portfolio-polish`

## Pull Request Rules
- Keep PR scope focused
- Include problem statement and solution summary
- Include validation steps (commands run, outputs inspected)
- Reference related issues when applicable

## Testing Recommendations
- Run targeted tests: `pytest tests/`
- Validate command help: `python src/cli.py --help`
- Validate affected subsystem CLI paths with sample config/input

## Reporting Issues
When opening issues, include:
- Environment (OS, Python version)
- Command executed
- Full error message
- Minimal reproducible input/sample config

## Review Expectations
Maintainers prioritize correctness, reproducibility, modularity, and documentation consistency.
