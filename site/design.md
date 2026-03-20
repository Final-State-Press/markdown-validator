# Design: markdown-validator

## 1. Purpose and Scope

`markdown-validator` is a rule-based linting tool for Markdown documents used
in static site generators (DocFX, Hugo).  It validates documents against a
declarative JSON rule set, checking both YAML front-matter metadata and the
HTML-rendered document body using XPath expressions.

The tool is used to:
- Enforce consistent document structure across large documentation repositories
- Validate metadata completeness (required keys, date freshness, topic values)
- Check heading hierarchy, section order, and content patterns
- Integrate with CI/CD pipelines as a validation gate

---

## 2. System Boundaries

```
┌─────────────────────────────────────────────────────────────────────┐
│  CLI Boundary                                                        │
│  Input:  CLI arguments (file paths, flags)                          │
│  Output: Exit code (0 = all pass, 1 = failures), stdout report      │
│  Entry:  markdown_validator.cli.main:cli                            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│  Service Boundary                                                    │
│  Input:  file paths (markdown + rule set)                           │
│  Output: ScanReport (Pydantic model, immutable)                     │
│  Entry:  Scanner.validate()                                         │
└──────────┬───────────────────────────────────┬──────────────────────┘
           │                                   │
┌──────────▼──────────┐            ┌───────────▼───────────────────────┐
│  Infrastructure     │            │  Domain                           │
│  Boundary           │            │  Boundary                         │
│  Input: file paths  │            │  Input: pure Python values        │
│  Output: domain     │            │  Output: bool / str               │
│  value objects      │            │  (no I/O, no side effects)        │
│  - ParsedDocument   │            │  - RuleModel (immutable)          │
│  - RuleSetModel     │            │  - ValidationResult (immutable)   │
└─────────────────────┘            └───────────────────────────────────┘
```

### Layer Dependency Rule

```
CLI  →  Services  →  Infrastructure  →  Domain
                ↘                  ↘
                 Domain              Domain
```

- **Domain** depends on nothing internal.
- **Infrastructure** depends only on Domain.
- **Services** depend on Domain and Infrastructure.
- **CLI** depends only on Services.

Violations of this rule (e.g., CLI importing from Infrastructure directly)
are prohibited.

---

## 3. Layer Responsibilities

### `markdown_validator.domain`

| Module | Responsibility |
|---|---|
| `models.py` | Pydantic contract models and frozen dataclasses (value objects) |
| `operators.py` | Pure comparison strategy functions — no I/O, no logging |
| `evaluator.py` | Apply a single `RuleModel` to a `ParsedDocument` → `ValidationResult` |
| `pos.py` | Thin NLTK wrapper for POS tagging and sentence counting |

**Domain does NOT**: read files, write files, log at INFO level, or reference
the infrastructure or services layers.

### `markdown_validator.infrastructure`

| Module | Responsibility |
|---|---|
| `parser.py` | Read a `.md` file → `ParsedDocument` (the only file reader for source docs) |
| `loader.py` | Read a `.json` rule-set file → `RuleSetModel` (Repository pattern) |
| `reporter.py` | Write `ScanReport` to JSON or CSV (the only file writer for output) |

**Infrastructure does NOT**: contain business logic, evaluate rules, or
interact with the CLI.

### `markdown_validator.services`

| Module | Responsibility |
|---|---|
| `scanner.py` | Facade: compose parser + loader + evaluator → `ScanReport` |
| `workflow.py` | Execute workflow step sequences against rule results |

**Services do NOT**: read/write files directly (delegated to infrastructure),
or handle CLI concerns.

### `markdown_validator.cli`

| Module | Responsibility |
|---|---|
| `main.py` | Click-based batch CLI — parse args, call Scanner, render output |
| `repl.py` | Interactive cmd.Cmd REPL — probe documents during rule development |

**CLI does NOT**: contain business logic or call infrastructure directly.

---

## 4. Design Patterns

### Strategy (`domain/operators.py`)

Each comparison operator is an independent `Callable[[str, str], bool]`
registered in `OPERATOR_REGISTRY`.

**Justification**: Operators can be substituted independently, tested in
isolation, and extended without modifying the evaluator.  Adding a new
operator (e.g., `>=`) requires only adding one function and one registry
entry.

### Repository (`infrastructure/loader.py`)

`RuleSetRepository.load(path)` is the single point for loading rule sets
from disk.

**Justification**: The Scanner service can be tested with an in-memory rule
set injected via the constructor, without any filesystem access.  This
enables fast, hermetic unit tests.

### Value Object (all models)

`ParsedDocument` is a frozen dataclass; all Pydantic models have
`model_config = {"frozen": True}`.

**Justification**: Eliminates accidental mutation across layer boundaries.
Frozen objects are inherently thread-safe and cacheable.

### Facade (`services/scanner.py`)

`Scanner` presents one `validate()` method over the
parse → load → evaluate → report pipeline.

**Justification**: CLI code remains simple; it does not need to know about
parsers, loaders, or evaluators.  The full pipeline is exercised with a
single call.

### Chain of Responsibility (`services/workflow.py`)

The `WorkflowEngine._dispatch()` method routes each workflow step to the
correct handler based on the `(source, target)` pattern.  Twelve patterns
are individually handled.

**Justification**: Each step type can be tested independently.  Adding a new
step type requires adding one `elif` branch without touching other patterns.

---

## 5. Contract Schemas

### Rule JSON Schema

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
      "name": "Check ms.topic",
      "steps": "S-1,1-E",
      "level": "Required",
      "fix": "Set ms.topic: tutorial in the front matter."
    }
  ]
}
```

**Schema notes:**
- `id` accepts strings (coerced to `int` at load time for backward compat)
- `level` and `mitigation` are optional on rules; defaults: `"Required"`, `""`
- Workflow `steps` accept both `S-1,1-E` and `(S,1)(1,E)` formats; normalised at load

### Pydantic Models (`domain/models.py`)

| Model | Role |
|---|---|
| `RuleModel` | Single rule (input contract, frozen) |
| `RulesSection` | Header + body rule lists; validates no duplicate IDs |
| `WorkflowModel` | Workflow step sequence (normalises step format on load) |
| `RuleSetModel` | Top-level rule set file schema |
| `ParsedDocument` | Immutable parsed document (frozen dataclass) |
| `ValidationResult` | Single rule evaluation outcome (output, frozen) |
| `ScanReport` | Aggregated scan results (output, frozen) |
| `WorkflowResult` | Single workflow execution result (output, frozen) |

---

## 6. Workflow Step Language Reference

A workflow is a string of comma-separated `<source>-<target>` tokens.
Twelve patterns are recognised:

| Pattern | Example | Meaning |
|---|---|---|
| `S-N` | `S-1` | Start: load rule N as the initial state |
| `N-D` | `1-D` | Rule N result becomes the decision point |
| `M-D` | `M-D` | Merge state becomes the decision |
| `T-N` | `T-2` | If decision is True, load rule N |
| `F-N` | `F-3` | If decision is False, load rule N |
| `T-R` | `T-R` | If decision is True, reverse (negate) it |
| `F-R` | `F-R` | If decision is False, reverse (negate) it |
| `N-M` | `2-M` | Rule N exits into merge state |
| `M-N` | `M-3` | Merge state exits to rule N |
| `M-E` | `M-E` | Merge state ends the workflow |
| `N-E` | `4-E` | Rule N result ends the workflow |
| `N-N` | `1-2` | Both rules must pass |

Example — simple rule check:
```
S-1,1-E
```

Example — conditional branch:
```
S-1,1-D,T-2,F-3,M-E
```
(Rule 1 is the decision; if True run rule 2, if False run rule 3, then end.)

---

## 7. Operator Reference

| Token | Name | Signature | Notes |
|---|---|---|---|
| `==` | Equal | `str == str` | Strips whitespace before comparing |
| `!=` | Not equal | `str != str` | Strips whitespace before comparing |
| `>` | Greater than | `int > int` | Both operands coerced to `int` |
| `<` | Less than | `int < int` | Both operands coerced to `int` |
| `[]` | Contains | `value in result` | Case-insensitive |
| `[:` | Starts with | `result.startswith(value)` | |
| `:]` | Ends with | `result.endswith(value)` | |
| `r` | Regex | `re.search(value, result)` | Python regex, DOTALL mode |
| `l` | Length | `len(result) < int(value)` | True if shorter than threshold |
| `s` | Sentence count | `sentences <= int(value)` | Body rules only, uses NLTK |
| `p<N>` | Part of speech | `pos_tag[N] == value` | e.g. `p1` checks word 1 |

---

## 8. Adding a New Operator

1. Add a function `op_myflag(result: str, value: str) -> bool` in
   `markdown_validator/domain/operators.py`.
2. Register it: `OPERATOR_REGISTRY["myflag"] = op_myflag`.
3. Add a unit test in `tests/unit/domain/test_operators.py`.
4. Document it in this table.

No other changes are required.

---

## 9. Known Limitations

- **NLTK data required**: `punkt_tab` and `averaged_perceptron_tagger_eng`
  must be downloaded before POS/sentence rules can run.
- **YAML front matter required**: All `.md` files must begin with a `---`
  block; plain Markdown without front matter is rejected.
- **XPath on flattened HTML**: The document body is rendered as standard HTML
  by the `markdown` library. The outline-based DOM described in the original
  README (where H3 is a child of H2) is **not** implemented; the DOM is flat.
  XPath queries must use positional predicates (e.g., `//h2[1]`) instead of
  structural nesting.
- **Concurrent scanning**: `Scanner.validate_directory()` processes files
  sequentially; parallelism is left to the caller (e.g., `concurrent.futures`).
- **No negation operator**: Absence assertions require brittle workflow
  inversion; a `negate` field is planned for v0.3.

For planned fixes to each of these limitations, see the [Product Roadmap](product/roadmap.md).
