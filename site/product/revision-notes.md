# Documentation Revision Notes — Thickening Pass

*Assessed: 2026-03-20 — Role: product leader + developer*

---

## Purpose

This document records the findings of a documentation audit conducted after the initial
consolidation pass. The goal is to identify where the documentation is factually correct
but insufficiently deep for a developer or content lead who needs to *actually use* the
tool or extend it. We call this "thickening": adding the worked examples, decision
context, and operational guidance that converts reference material into knowledge.

---

## Audit findings by document

### index.md (Home)

**Thin:** The page explains the mechanics but not the problem. A new reader doesn't
understand *why* a documentation team at scale needs this tool, what "large repository"
means in practice, or what a good outcome looks like. The score (`report.score`) is
mentioned in the API example with no explanation of what it means or how teams use it.

**Workflow is invisible:** The home page mentions workflows in passing ("Rules can be
chained into workflows") but gives no sense of what problem they solve or when you would
use them.

**Revisions applied:**
- Added "The problem this solves" section with a concrete scale context
- Added "Workflows" subsection in the How it works section
- Added "CI integration" one-liner with link to CLI reference
- Clarified what `report.score` means

---

### rules-reference.md

**Thin:** All tables, no examples. A writer authoring their first rule set has no
reference point for what a valid `date` rule looks like, what `pattern` does differently
from `r`, or how comma-separated multi-values actually behave.

**Missing gotchas:** The `[]` operator is documented as "Contains" but rule authors
frequently use it for absence checks (which requires workflow inversion). The
multi-element XPath + equality problem is completely absent. These are the most
common sources of incorrect rules.

**Workflow section redirects:** "See DESIGN.md" is not sufficient for a rule author
who needs to write their first workflow.

**Revisions applied:**
- Added "Flag examples" section with one complete rule per flag type
- Added "Operator examples" with non-obvious operators (`date`, `r`, `l`, `s`, `p<N>`)
- Added "Common mistakes" section: multi-element equality, comma parsing, negation patterns
- Expanded "Workflow step language" to include two worked examples inline

---

### architecture.md

**Thin:** Lists the modules and their responsibilities but doesn't answer the developer's
key question: *where do I touch the code to make a change?* The extension points
(operators, parser, reporter) are implicit in DESIGN.md but not surfaced here.

**Test strategy absent:** The test suite has 189 tests at 95.68% coverage, organised to
mirror the layer structure. This is worth documenting — it tells a new contributor where
to find and add tests.

**Revisions applied:**
- Added "Extension points" section: where to add an operator, a flag, a reporter format
- Added "Test organisation" section mirroring layer structure
- Added link to SRS for requirements traceability

---

### cli-reference.md

**Thin on output:** No example of what a text report actually looks like. A user
integrating into CI doesn't know whether to parse the text output, use `--format json`,
or something else.

**No CI guidance:** The primary deployment target for this tool is CI pipelines, but the
documentation has no example of a GitHub Actions step or equivalent.

**Revisions applied:**
- Added "Sample text output" block showing a realistic pass/fail report
- Added "CI integration" section with GitHub Actions example
- Added note on exit codes and their meaning in pipeline context

---

## What was NOT changed

- **design.md**: Already the most substantive document. Minor note added about Known
  Limitations pointing to the roadmap.
- **product/assessment.md**: Factual, complete, visually well-structured.
- **product/roadmap.md**: Well-structured; no thickening needed yet.
- **srs.md**: Comprehensive for the current version; will need update when v0.3 ships.
- **API docs** (`api/*.md`): These are auto-generated from docstrings; thickening those
  docs means improving the source docstrings, which is a separate engineering task.
