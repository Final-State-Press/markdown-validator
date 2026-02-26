# Markdown Validator

Rule-based Markdown document validation for static site content.

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)

## Overview

`markdown-validator` validates Markdown files against a declarative JSON rule set.
Rules can check YAML front-matter metadata and document body content using XPath.
Designed for large documentation repositories built with DocFX, Hugo, or similar
static site generators.

## Installation

```bash
pip install markdown-validator
```

For development:

```bash
git clone https://github.com/mattbriggs/markdown-validator
cd markdown-validator
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick start

```bash
# Validate a single file
md-validate validate docs/article.md --rules rules/tutorial.json

# Validate a directory (recursive)
md-validate validate docs/ --rules rules/tutorial.json

# JSON output
md-validate validate docs/article.md --rules rules/tutorial.json --format json

# Interactive REPL for rule development
md-validate repl
```

## Python API

```python
from markdown_validator import Scanner

scanner = Scanner()
report = scanner.validate("docs/article.md", "rules/tutorial.json")

print(f"Passed: {report.passed}")
print(f"Score:  {report.score}/{report.total_rules}")

for result in report.results:
    status = "✓" if result.passed else "✗"
    print(f"  {status} [{result.rule_id}] {result.rule_name}")
```

## Rule set format

```json
{
  "rules": {
    "header": [
      {
        "id": 1,
        "name": "topic-must-be-tutorial",
        "type": "header",
        "query": "ms.topic",
        "flag": "value",
        "operation": "==",
        "value": "tutorial",
        "level": "Required",
        "mitigation": "Set ms.topic: tutorial in the front matter."
      }
    ],
    "body": [
      {
        "id": 2,
        "name": "must-have-h1",
        "type": "body",
        "query": "/html/body/h1",
        "flag": "count",
        "operation": "==",
        "value": "1",
        "level": "Required",
        "mitigation": "The document must have exactly one H1 heading."
      }
    ]
  },
  "workflows": []
}
```

See [docs/rules-reference.md](docs/rules-reference.md) for the full operator and flag reference.

## Architecture

The project follows a strict domain / infrastructure / services / CLI layering:

```
CLI → Services → Infrastructure → Domain
```

See [DESIGN.md](DESIGN.md) for the full architecture, design patterns, and extension guide.

## Development

```bash
# Run tests with coverage
pytest

# Lint
ruff check markdown_validator/

# Type check
mypy markdown_validator/

# Build docs
mkdocs serve
```

## License

MIT
