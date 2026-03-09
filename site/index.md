# Markdown Validator

Rule-based Markdown document validation for static site content.

## What it does

`markdown-validator` validates Markdown files against a declarative JSON rule set. It checks:

- **YAML front-matter metadata** — required keys, expected values, date freshness
- **Document body content** — heading structure, section order, text patterns, character limits

It is designed for large documentation repositories built with static site generators such as DocFX and Hugo.

## Quick start

```bash
# Install
pip install markdown-validator

# Validate a single file
md-validate validate docs/article.md --rules rules/tutorial.json

# Validate all .md files in a directory
md-validate validate docs/ --rules rules/tutorial.json --output reports/

# Interactive REPL for rule development
md-validate repl
```

## How it works

1. A **rule set** JSON file defines assertions about the document.
2. Each rule targets either the **metadata** (YAML front matter) or the **body** (via XPath on the rendered HTML).
3. Rules can be chained into **workflows** for conditional logic.
4. The tool outputs a **score** (passing rules / total rules) and a per-rule pass/fail report.

## Example rule set

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
  "workflows": [
    {
      "name": "topic-check",
      "steps": "S-1,1-E",
      "fix": "Set ms.topic: tutorial in the front matter."
    }
  ]
}
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
    if not result.passed:
        print(f"      → {result.mitigation}")
```
