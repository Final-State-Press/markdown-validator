# Markdown Validator

Rule-based Markdown document validation for static site content.

## The problem this solves

Documentation repositories for large software products can contain thousands of Markdown
files contributed by dozens of authors. Without automated checks, metadata becomes
inconsistent (wrong `ms.topic` values, stale `ms.date`, missing `description`), and
structural conventions drift (articles missing an H1, tutorials without a "Prerequisites"
section, headings that use numbered lists instead of titles).

Manual review at scale is not viable. `markdown-validator` runs these checks
automatically — in a developer's local environment and as a CI gate — so that a
content lead can define the rules once and have them applied consistently across every
article in the repository.

A realistic repository might have 40–50 rules covering metadata completeness, heading
hierarchy, required sections, link conventions, and title length. The tool produces a
per-file score (passing rules / total rules) and a per-rule pass/fail report with
remediation guidance.

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

### Workflows

Simple rule lists can't express conditional dependencies. Workflows fill this gap.
For example: "if the document has no H2 headings, also check that it has no H3 headings"
cannot be expressed as two independent rules (H3s are only a problem if H2s are missing).
The workflow mini-language handles exactly these cases. See the
[Rules Reference — Workflow step language](rules-reference.md#workflow-step-language)
for the full reference.

### CI integration

```bash
md-validate validate docs/ --rules rules/tutorial.json
echo "Exit code: $?"  # 0 = all Required rules passed; 1 = failures
```

See the [CLI Reference](cli-reference.md) for output formats, directory scanning, and
GitHub Actions integration.

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

# report.passed  — True if all Required rules passed
# report.score   — count of passing rules
# report.total_rules — total rules evaluated
print(f"Passed: {report.passed}")
print(f"Score:  {report.score}/{report.total_rules}")

for result in report.results:
    status = "✓" if result.passed else "✗"
    print(f"  {status} [{result.rule_id}] {result.rule_name}")
    if not result.passed:
        print(f"      → {result.mitigation}")
```

A score of `26/26` means every rule passed. A score of `24/26` means two rules failed;
the report identifies which rules and what to fix. In CI, a failing `Required` rule
sets the exit code to `1`, blocking the merge.
