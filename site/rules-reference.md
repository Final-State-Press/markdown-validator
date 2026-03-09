# Rules Reference

## Rule fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | integer | Yes | Unique rule identifier (strings coerced to int) |
| `name` | string | Yes | Human-readable rule name |
| `type` | `"header"` or `"body"` | Yes | Whether to query metadata or document body |
| `query` | string | Yes | Metadata key (header) or XPath expression (body) |
| `flag` | string | Yes | Processing mode (see Flags table) |
| `operation` | string | Yes | Comparison operator (see Operators table) |
| `value` | string | Yes | Expected value; comma-separated for multi-value checks |
| `level` | `"Required"` or `"Suggested"` | No | Default: `"Required"` |
| `mitigation` | string | No | Remediation message shown on failure |

## Flags

| Flag | Applies to | Description |
|---|---|---|
| `value` | header | Evaluate the metadata value with `operation` and `value` |
| `check` | header | True if the key exists (ignores `operation`/`value`) |
| `date` | header | Compare metadata value as a date |
| `pattern` | header | Match metadata value against `value` as a regex |
| `count` | body | Count matching XPath nodes; compare with `operation`/`value` |
| `text` | body | Extract text of first matching XPath node |
| `dom` | body | Extract element tag names of matching nodes |
| `all` | body | Full plain-text content of the page |

## Operators

| Token | Name | Notes |
|---|---|---|
| `==` | Equal | Strips whitespace |
| `!=` | Not equal | Strips whitespace |
| `>` | Greater than | Numeric comparison |
| `<` | Less than | Numeric comparison |
| `[]` | Contains | Case-insensitive |
| `[:` | Starts with | |
| `:]` | Ends with | |
| `r` | Regex match | Python re.search, DOTALL mode |
| `l` | Length limit | `len(result) < int(value)` |
| `s` | Max sentences | `sentence_count <= int(value)` |
| `p<N>` | Part of speech | `p1` = first word POS tag; uses Penn Treebank tags |

## Workflow step language

See [DESIGN.md — Workflow Step Language Reference](../DESIGN.md#6-workflow-step-language-reference).
