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

**`level` and CI exit codes**: A `Required` rule that fails sets the CLI exit code to
`1`, blocking a CI merge gate. A `Suggested` rule that fails is reported but does not
change the exit code. Use `Suggested` for style recommendations that should not block
publication.

---

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

### Flag examples

**`value`** — check that a metadata field equals an expected string:
```json
{
  "id": 1, "name": "topic-must-be-tutorial", "type": "header",
  "query": "ms.topic", "flag": "value", "operation": "==", "value": "tutorial",
  "mitigation": "Set ms.topic: tutorial in the front matter."
}
```

**`check`** — verify a required metadata key is present (value doesn't matter):
```json
{
  "id": 2, "name": "description-must-exist", "type": "header",
  "query": "description", "flag": "check", "operation": "==", "value": "true",
  "mitigation": "Add a description field to the front matter."
}
```

**`date`** — check that `ms.date` is no more than 365 days in the past.
The `value` field is the maximum age in days; the `operation` is `<` (age must be less
than the threshold):
```json
{
  "id": 3, "name": "date-must-be-fresh", "type": "header",
  "query": "ms.date", "flag": "date", "operation": "<", "value": "365",
  "mitigation": "Update ms.date to a date within the last year."
}
```
The metadata value must be a date string parseable by Python's `dateutil` (e.g.
`2026-01-15`). The comparison is: `(today − ms.date).days < int(value)`.

**`pattern`** — match the metadata value against a regex (alias for `r` on header fields):
```json
{
  "id": 4, "name": "author-github-format", "type": "header",
  "query": "author", "flag": "pattern", "operation": "r",
  "value": "^[a-z0-9-]+$",
  "mitigation": "author must be a lowercase GitHub username (letters, numbers, hyphens)."
}
```

**`count`** — count matching XPath nodes:
```json
{
  "id": 5, "name": "must-have-exactly-one-h1", "type": "body",
  "query": "/html/body/h1", "flag": "count", "operation": "==", "value": "1",
  "mitigation": "The document must have exactly one H1 heading."
}
```

**`text`** — extract the text content of the first matching XPath node:
```json
{
  "id": 6, "name": "h1-must-start-with-tutorial", "type": "body",
  "query": "/html/body/h1", "flag": "text", "operation": "[:","value": "Tutorial:",
  "mitigation": "H1 must begin with 'Tutorial:' for tutorial articles."
}
```

**`dom`** — extract element tag names (useful for checking heading order):
```json
{
  "id": 7, "name": "first-heading-after-h1-must-be-h2", "type": "body",
  "query": "/html/body/*[2]", "flag": "dom", "operation": "==", "value": "h2",
  "mitigation": "The second element in the body must be an H2."
}
```

**`all`** — run a check against the entire plain-text body:
```json
{
  "id": 8, "name": "body-must-not-be-empty", "type": "body",
  "query": "/html/body", "flag": "all", "operation": ">", "value": "0",
  "mitigation": "The document body must not be empty."
}
```

---

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
| `r` | Regex match | Python `re.search`, DOTALL mode |
| `l` | Length limit | `len(result) < int(value)` — True if shorter than threshold |
| `s` | Max sentences | `sentence_count <= int(value)` — requires NLTK |
| `p<N>` | Part of speech | `p1` = first word POS tag; uses Penn Treebank tags |

### Operator examples for non-obvious operators

**`r` (regex)** — check that the title matches a pattern:
```json
{
  "flag": "text", "operation": "r", "value": "^Tutorial: [A-Z]",
  "mitigation": "Title must match 'Tutorial: ' followed by a capital letter."
}
```

**`l` (length limit)** — ensure the title is under 60 characters:
```json
{
  "flag": "text", "operation": "l", "value": "60",
  "mitigation": "Title must be under 60 characters."
}
```

**`s` (sentence count)** — limit the intro paragraph to 3 sentences:
```json
{
  "flag": "all", "operation": "s", "value": "3",
  "mitigation": "Introduction must be no more than 3 sentences."
}
```
Requires NLTK corpora. Run `python -m nltk.downloader punkt_tab averaged_perceptron_tagger_eng` after installing the package.

**`p<N>` (part of speech)** — check that the third word of the H1 is a verb (`VB`):
```json
{
  "flag": "text", "operation": "p3", "value": "VB",
  "mitigation": "The third word of the H1 should be a base-form verb."
}
```
Uses Penn Treebank tags: `NN` (noun), `VB` (base verb), `VBZ` (3rd-person verb),
`JJ` (adjective), `RB` (adverb). Position is 1-indexed.

---

## Common mistakes

### Multi-element XPath + equality

When an XPath returns multiple elements and you use `==`, the evaluator checks that
**every** element satisfies the assertion (logical AND). This is almost always wrong.

**Wrong**: "The second-to-last H2 is 'Clean up resources'"
```json
{ "query": ".//h2[last()]/preceding-sibling::h2", "flag": "text", "operation": "==" }
```
This XPath returns *all* H2s before the last one. Requiring all of them to equal
`'Clean up resources'` fails on any document with more than two H2s.

**Right**: Target the specific element directly:
```json
{ "query": ".//h2[last()-1]", "flag": "text", "operation": "==" }
```

### Comma-separated multi-values

The `value` field is split on `,` to produce a list for operators that support
multi-value checks (`[]`). The value `"guide, article, topic"` becomes three checks:
`"guide"`, `" article"`, `" topic"` (note the leading space). Whitespace is stripped
before comparison, so this works in practice — but a literal comma inside a single
expected value has no escape mechanism.

### Expressing absence (no negation operator)

The rule language has no built-in negation. To express "the title must NOT contain the
word 'guide'", the idiomatic (but fragile) approach is to use workflow branching with a
known-passing rule as a sentinel. The upcoming `negate: true` field (planned for v0.3)
will eliminate this pattern. See the [Roadmap](product/roadmap.md#negation-operator-v03)
for details.

---

## Workflow step language

A workflow is a comma-separated string of `<source>-<target>` tokens that chains rule
evaluations with conditional branching.

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

### Worked example 1 — simple rule check

```
S-1,1-E
```

Start with rule 1. Rule 1's result ends the workflow. This is the simplest possible
workflow: a single rule.

### Worked example 2 — conditional branch

```
S-1,1-D,T-2,F-3,2-M,3-M,M-E
```

Rule 1 is evaluated and its result becomes the decision. If True, rule 2 runs; if False,
rule 3 runs. Both rules exit into merge state, which ends the workflow. The overall
workflow passes if the branch that executed passed.

**Practical use**: Rule 1 checks `ms.topic == "tutorial"`. Rule 2 checks that the H1
starts with "Tutorial:". Rule 3 checks that the H1 starts with "How to". This enforces
topic-type-specific H1 conventions in a single workflow.

### Worked example 3 — conditional presence check

```
S-38,38-D,T-39,F-38,39-M,M-E
```

Rule 38 counts H2 headings. If the count is > 0 (True), rule 39 checks for H3s. If there
are no H2s (False), rule 38's own (passing) result feeds into merge. This implements
"H3s are only required if H2s are present."

For the full technical reference, see [Design — Workflow Step Language](design.md#6-workflow-step-language-reference).
