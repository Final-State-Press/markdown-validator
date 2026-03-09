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

## `md-validate repl`

Start the interactive REPL for rule development.

```
md-validate repl
```

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

> quit
```
