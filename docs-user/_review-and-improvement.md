# Documentation Review and Improvement Notes

*Pass 2 — Audience simulation + SEO/scannability + Azure/AWS/Oracle/GCloud benchmark*
*Reviewed: 2026-03-20*

---

## Part A: Audience Simulation Review

### As the end user (technical writer, blocked pull request)

**Simulation**: I have a failed CI run. I go to the documentation to fix my article.

**Path I take:**
1. I land on the home page — but the home page for this DITA set has no obvious entry
   point for "my PR is blocked." I need a "If your PR was just blocked, start here"
   callout at the top.
2. I eventually find `t_read-validation-report.dita` — this is the most important
   topic for me. It is complete and empathetic. ✓
3. The front-matter failure table is excellent. The body failure table covers H1 and
   H2; it does not mention the case where a body rule about a specific field value
   (e.g., title length) fails. This is a gap.
4. `t_install.dita` — clear and complete. The Windows/macOS split is good. ✓
5. `t_download-nltk.dita` — found via the `postreq` in `t_install`. The tip suggesting
   you ask your content lead whether NLTK rules are in use is excellent empathy.
6. `t_integrate-github-actions.dita` — comprehensive. The `if: always()` explanation
   is helpful detail that I would have missed. ✓
7. `r_cli-options.dita` — scannable and complete. ✓

**Gaps identified:**
- Missing: "Your PR was blocked — here is the fastest path to fixing it" entry point.
  This needs to be addressed in the home topic or a landing concept.
- The `t_read-validation-report.dita` body failure table should include "text rule
  failures" (when the body text fails a regex or length check).
- `c_what-is-markdown-validator.dita` does not tell me where to get the rule set
  file from. "Ask your content lead" is fine but should be more explicit about
  where rule sets typically live in the repo.

---

### As the rule creator (content lead, deploying a new rule)

**Simulation**: I need to enforce that every tutorial's `ms.date` is within 12 months.
I have never written a date rule before.

**Path I take:**
1. I read `c_rule-anatomy.dita` — good, I understand the nine fields. ✓
2. I search for "date" — I find `r_flags.dita`. The date flag example is clear and
   includes the formula `(today - ms.date).days < 365`. ✓
3. I write the rule and want to test it. I go to `t_start-repl.dita` then
   `t_test-rule-repl.dita`. The test task is good but it does not show how to test
   a date rule specifically — the REPL `get` command shows the raw date string,
   but I can't tell if the comparison will work. This needs an example.
4. I find `c_rule-design-patterns.dita` — the date-freshness pattern is exactly what
   I needed. Good placement. ✓
5. `t_deploy-rule-set.dita` — the pre-deploy scan and notification steps are excellent
   operational guidance. ✓

**Gaps identified:**
- `t_test-rule-repl.dita` does not include an example of testing a date rule (where
  the `eval` output might not be intuitive since it compares age in days, not the
  date string). Add a worked example for date rules.
- `c_rule-governance.dita` should include an example changelog entry (it currently
  references one but the format shown is minimal). ✓ Already addressed.
- `c_known-limitations.dita` should cross-link to `ts_rule-never-passes.dita` since
  multi-element equality is a common cause of debugging sessions.

---

## Part B: SEO and Scannability Assessment

### Scannability audit

All topics have:
- ✓ Short description (abstracts) — present and informative in all topics
- ✓ Descriptive section headings — all topics use `<section>` with `<title>`
- ✓ Tables for reference information — used consistently in reference topics
- ✓ Code blocks for all command-line examples — present throughout

Improvements needed:
- **Reference topics** need anchors at every table row for deep-linking from other
  topics. DITA IDs on `<row>` elements are not standard; use `<section>` wrappers per
  operator group in `r_operators.dita` to enable deep-links.
- **`c_how-validation-works.dita`** has dense prose in the "What the score means"
  section. The distinction between Required and Suggested score impact could be
  in a table for faster scanning.
- Task topics should have a **"Time required"** or **"Difficulty"** indicator in
  the prereq section — not for this version, but a future improvement.

### SEO audit

All topics have:
- ✓ Primary keyword phrase in `<title>`
- ✓ `<othermeta name="description">` meta description
- ✓ `<keywords>` in prolog

The following titles are improved below:
- `t_read-validation-report.dita` title could be more search-shaped:
  "Read and act on a validation report" → "How to read a markdown-validator report"
- `c_ci-integration-overview.dita` title could be sharper:
  "How markdown-validator fits into your CI/CD pipeline" is good for SEO ✓

---

## Part C: Azure / AWS / Oracle / Google Cloud Benchmark

### What best-in-class documentation has that this set lacks

**Azure Docs strengths (docs.microsoft.com):**
1. Every concept page has a **"Prerequisites" callout** at the very top — before
   any prose — telling you exactly what you need to know before reading.
   *Gap*: Our concepts go directly into content. Add a `<note type="prerequisite">`
   to concept pages where prior knowledge is assumed.
2. Azure uses **"In this article"** navigation at the top of long pages.
   DITA does not have a built-in TOC-in-topic construct, but we can simulate this
   with a `<shortdesc>` that lists sections, or a `<note>` at the top.
3. Azure includes **"Next steps"** at the end of every task, which we do have. ✓

**AWS Docs strengths (docs.aws.amazon.com):**
1. AWS provides **end-to-end scenario tutorials** — "Set up validation from scratch
   for a new repository" — that walk a user through multiple connected tasks in
   sequence. We have individual tasks but no end-to-end scenario.
   *Gap*: Add a `t_end-to-end-setup.dita` scenario task (see below).
2. AWS reference pages have **anchors on every row** for deep-linking.
   *Gap*: Add `id` attributes to key table rows and sections in reference topics.
3. AWS uses **"Note," "Warning," "Tip," and "Important"** admonitions consistently.
   *Gap*: We have some `<note>` elements but inconsistently. Audit and add.

**Oracle Docs strengths:**
1. Oracle documentation includes **explicit workflow diagrams** — numbered diagrams
   showing where the current task sits in a larger process.
   *Gap*: The CI integration overview concept would benefit from a workflow diagram
   (which we do describe in prose but could be a numbered step diagram).
2. Oracle cross-references are very consistent — every reference concept links to
   the task that uses it.
   *Gap*: `r_operators.dita` should link to `t_write-body-rule.dita`. Add.

**Google Cloud Docs strengths (cloud.google.com/docs):**
1. Google uses **"Before you begin"** consistently with a numbered checklist
   at the start of every task — more visible than our `<prereq>` section.
   Our `<prereq>` elements are correctly structured but use variable formatting.
   Standardize to a numbered list inside `<prereq>`.
2. Google docs always include **"What's next"** at the end of concept pages.
   *Gap*: Our concept pages have "Next steps" sections but they are inconsistently
   placed and formatted. Standardize to a final `<section id="whats-next">` in
   every concept.
3. Google provides **"Try it yourself"** interactive examples or "Quickstart"
   paths. *Gap*: Add a quick-start scenario topic.

---

## Part D: Improvement Plan

### Priority 1 — High impact, low effort

1. Add "Your PR is blocked" fast-path callout to `c_what-is-markdown-validator.dita`
2. Add scenario task `t_end-to-end-setup.dita` linking all user-guide tasks in sequence
3. Standardize "What's next" section at the end of every concept topic
4. Add `id` attributes to key sections in all reference topics for deep-linking
5. Cross-link `c_known-limitations.dita` from `ts_rule-never-passes.dita`
6. Add a date-rule testing example to `t_test-rule-repl.dita`

### Priority 2 — Medium impact

7. Add "In this topic" summary `<note>` to long concept pages
   (`c_rule-anatomy`, `c_workflow-language-overview`, `c_rule-design-patterns`)
8. Audit and standardize `<note type="...">` admonitions (tip, important, caution,
   warning) across all topics
9. Add `id` attributes to each operator row in `r_operators.dita`
10. Add cross-reference from `r_operators.dita` to `t_write-body-rule.dita`

---

## Part E: Improvements Applied

The following changes are applied directly to the affected files (see edits below
this document). Inline improvements rather than new files where possible.

### Applied to c_what-is-markdown-validator.dita
- Added "If your pull request was blocked" fast-path `<note type="important">`

### Applied to t_test-rule-repl.dita
- Added date-rule testing example with `get` command comparison

### Applied to r_operators.dita
- Added cross-reference to t_write-body-rule.dita in the notes section

### Applied to ts_rule-never-passes.dita
- Added cross-reference to c_known-limitations.dita

### New file: t_end-to-end-setup.dita (added to user guide)
- Scenario task linking install → NLTK → validate → GitHub Actions

### Concept pages
- Standardized "What's next" to `<section id="whats-next">` format
  (already correct in most topics — confirmed consistent)
