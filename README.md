App to train for danish citizenship

## Python Environment

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Setup

1. Install [Poetry](https://python-poetry.org/docs/#installation) if you haven't already.
2. Install dependencies:
   ```bash
   poetry install
   ```

### Running Scripts

You can run the extraction scripts using `poetry run`:

```bash
poetry run python src/extraction/extract_ch1.py
```

### Development

Format code:
```bash
poetry run black .
```

Lint code:
```bash
poetry run ruff check .
```
