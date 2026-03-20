# CLI Reference

## `md-validate validate`

Validate a Markdown file or directory against a rule set.

```
md-validate [--verbose] [--quiet] validate TARGET --rules RULES [options]
```

### Arguments

| Argument | Description |
|---|---|
| `TARGET` | Path to a `.md` file or directory (recursive) |

### Options

| Option | Default | Description |
|---|---|---|
| `--rules / -r` | required | Path to the rule-set JSON file |
| `--output / -o` | — | Directory to write report files |
| `--format / -f` | `text` | Output format: `text`, `json`, or `csv` |
| `--workflows / --no-workflows` | enabled | Run workflow chains after evaluation |
| `--verbose / -v` | off | Enable DEBUG logging |
| `--quiet / -q` | off | Suppress all non-error output |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | All Required rules passed |
| `1` | One or more Required rules failed |

The exit code is what CI systems use to gate a build. `Suggested`-level rule failures
are reported but do not change the exit code.

### Examples

```bash
# Basic validation
md-validate validate article.md --rules rules/tutorial.json

# JSON output
md-validate validate article.md --rules rules/tutorial.json --format json

# Validate directory, save CSV reports
md-validate validate docs/ --rules rules/tutorial.json --format csv --output reports/

# Verbose debug output
md-validate --verbose validate article.md --rules rules/tutorial.json
```

### Sample text output

```
Validating: docs/tutorial-deploy-app.md
Rule set:   rules/tutorial.json

  ✓  [1]  topic-must-be-tutorial
  ✓  [2]  must-have-h1
  ✓  [3]  h1-must-start-with-tutorial
  ✗  [4]  description-must-exist
           → Add a description field to the front matter.
  ✓  [5]  ms-date-must-be-fresh
  ✗  [6]  title-under-60-chars
           → Title must be under 60 characters.
  ✓  [7]  must-have-prerequisites-h2
  ✓  [8]  must-have-next-steps-h2

Score: 6/8   FAILED (2 Required rules failed)
```

When all rules pass:

```
Score: 8/8   PASSED
```

---

## CI integration

### GitHub Actions

```yaml
name: Validate docs

on:
  pull_request:
    paths:
      - 'docs/**/*.md'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install markdown-validator
        run: |
          pip install markdown-validator
          python -m nltk.downloader punkt_tab averaged_perceptron_tagger_eng

      - name: Validate docs
        run: md-validate validate docs/ --rules rules/tutorial.json --format json --output reports/

      - name: Upload reports
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: validation-reports
          path: reports/
```

The step exits with code `1` if any `Required` rule fails, blocking the PR merge.
Uploading reports as artifacts makes it easy for authors to see which rules failed
without reading the raw log.

### Using JSON output in scripts

```bash
result=$(md-validate validate docs/ --rules rules/tutorial.json --format json)
failures=$(echo "$result" | jq '[.results[] | select(.passed == false)] | length')
echo "Failed rules: $failures"
```

---

## `md-validate repl`

Start the interactive REPL for rule development.

```
md-validate repl
```

The REPL lets you load a Markdown file, inspect its metadata and HTML, run XPath
queries, and evaluate rule JSON objects interactively. Use it to author and debug rules
before committing them to a rule-set file.

### REPL commands

| Command | Description |
|---|---|
| `load <path>` | Load a Markdown file |
| `dump metadata` | Print the loaded file's metadata as JSON |
| `dump html` | Print the rendered HTML |
| `query <xpath> [flag]` | Run an XPath query (flags: `text`, `count`, `dom`) |
| `get <key>` | Get a metadata value by key |
| `eval <json-rule>` | Evaluate a rule JSON object against the loaded file |
| `quit` / `exit` | Exit the REPL |

### REPL example session

```
> load docs/article.md
Loaded: /abs/path/docs/article.md
  Metadata keys : ['title', 'ms.topic', 'ms.date', 'author']

> get ms.topic
ms.topic: tutorial

> query /html/body/h1 text
Result: ['My Tutorial Title']

> query /html/body/h2 count
Result: [3]

> eval {"id":1,"name":"topic-check","type":"header","query":"ms.topic","flag":"value","operation":"==","value":"tutorial"}
PASS: rule id=1 name='topic-check'

> query /html/body/h2 text
Result: ['Prerequisites', 'Deploy the app', 'Clean up resources']

> quit
```

**Workflow for authoring a new rule:**

1. `load` the document you are writing the rule for.
2. `query` your XPath expression with the relevant flag (`text`, `count`, `dom`) to confirm it returns what you expect.
3. `eval` a complete rule JSON object to see pass/fail before adding it to the rule-set file.
4. Repeat with `load` on a document that should fail the rule to confirm the rule catches the problem.
