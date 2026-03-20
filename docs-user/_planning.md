# DITA Content Architecture: Planning Document
## markdown-validator End-User Documentation

*Author: Technical Communication Team — 2026-03-20*

---

## 1. Initial Outline (Draft 1)

### User Guide
- What is markdown-validator? (concept)
- How validation works (concept)
- Validation levels: Required vs. Suggested (concept)
- CI/CD integration overview (concept)
- Install markdown-validator (task)
- Download NLTK language data (task)
- Validate a single file (task)
- Validate a directory (task)
- Set the output format (task)
- Save reports to a directory (task)
- Add markdown-validator to GitHub Actions (task)
- CLI options reference (reference)
- Exit codes reference (reference)
- Validation report fields reference (reference)

### Rule Creator Guide
- Rule sets overview (concept)
- Anatomy of a rule (concept)
- Workflow language overview (concept)
- Rule set governance (concept)
- Create a rule set file (task)
- Write a header rule (task)
- Write a body rule (task)
- Write a workflow (task)
- Start the interactive REPL (task)
- Test a rule with the REPL (task)
- Deploy a rule set (task)
- Rule fields reference (reference)
- Flags reference (reference)
- Operators reference (reference)
- Workflow step patterns reference (reference)
- REPL commands reference (reference)

### Troubleshooting
- NLTK LookupError on first run
- ParseError: file has no front matter
- A rule always fails even on a valid document
- XPath expression returns unexpected results
- Validation step fails in CI pipeline

### Shared
- Glossary

---

## 2. Outline Review

### 2a. As the End User (technical writer, content author)

**What I need:**
I have just been told my PRs are being blocked by a validation tool I've never heard of.
I need to understand what it is, install it locally, and get my article passing — fast.

**Gaps in the outline:**
- WHERE is "understand the failure report so I can fix my document"? The task
  "Validate a single file" ends when the command runs. I need a task or concept that
  maps the output back to what I need to change.
- There is no "fix common front-matter errors" task. Authors hit the same 5 problems
  (wrong ms.topic value, missing description, stale ms.date) over and over.
- "Download NLTK language data" is a task that many users will encounter with no
  warning. It feels orphaned. It needs to be part of the installation flow or clearly
  signposted as a post-install step.
- I don't know what a "rule set" is and I don't need to. But I need to know WHERE
  to get the rule set file my team uses. This is missing entirely.
- The relationship between "Required" failures (blocks CI) and "Suggested" (does not)
  should be surfaced earlier — ideally in the install task, not in a separate concept.
- I want an "understanding my score" section. 24/26 means something; I want to know
  how to bring it to 26/26.

**Empathy gaps:**
- The tone assumes technical proficiency. Many technical writers are not comfortable
  with the command line. The install task needs "how do I open a terminal?" guidance
  at least as a link.
- The word "XPath" appears in the outline; end users should never see it.

### 2b. As the Rule Creator (content lead, editorial lead)

**What I need:**
I manage a documentation repository of 800 articles. I need to author and maintain
a rule set that enforces our editorial guide. I need to know how to express every
type of check I might need, how to test rules before deploying them, and how to
communicate rule changes to my team of writers.

**Gaps in the outline:**
- "Anatomy of a rule" is too abstract. I need worked examples that map editorial
  requirements to rule JSON. E.g., "the ms.date must be within the last 12 months"
  should appear as a complete example.
- The workflow language overview doesn't explain *when* to use a workflow vs. a
  simple rule list. I don't know what conditional logic I need until I understand
  the problem it solves.
- There is no "rule set design patterns" content. I need patterns like:
  "how to express absence," "how to enforce section order," "how to check conditional
  metadata."
- "Deploy a rule set" is vague. Where does the rule set live? How do I version it?
  How do I communicate changes to authors?
- Testing workflows (not just individual rules) is missing from the REPL task.
- The rule governance concept is thin. I need content on: when to make a rule
  Required vs. Suggested, how to deprecate a rule, migration strategy when changing
  a rule's value.
- A "Known limitations" topic is needed so I don't waste hours writing rules that
  will silently fail (flat DOM, negation gap).

### 2c. As the Technical Communicator (author of this documentation set)

**Content architecture concerns:**
- The troubleshooting section needs a topic for "a rule always evaluates to pass
  even when it should fail" — the negation/inversion problem is the single most
  complex bug authors encounter.
- The glossary is essential. Terms like "front matter," "XPath," "flag," "operator,"
  and "workflow" have overloaded meanings. Define them early, link consistently.
- The REPL tasks (start REPL + test a rule) should be separate tasks with a clear
  parent concept explaining what the REPL is *for* (developers don't need this
  explanation; content leads do).
- The content needs a "your workflow" framing device — a map of how these tasks
  fit into the authoring and governance lifecycle. Without it, users don't know
  which docs are for them.
- SEO: every topic needs a primary keyword phrase in the title and short description.
  Titles should be search-query shaped ("How to validate a Markdown file").
- Reference topics will be the most-visited pages. They need anchors at every row.
- The "add to GitHub Actions" task should include the NLTK download step — currently
  it's split across two tasks and a user following the CI task will miss it.

---

## 3. Revised Outline (Final)

### User Guide
**Concepts:**
- c_what-is-markdown-validator — What markdown-validator does (concept)
- c_how-validation-works — How validation works: parse, evaluate, report (concept)
- c_validation-levels — Required vs. Suggested validation levels (concept)
- c_ci-integration-overview — How markdown-validator fits into CI/CD pipelines (concept)

**Tasks:**
- t_install — Install markdown-validator (task)
- t_download-nltk — Download NLTK language data for sentence and POS rules (task)
- t_validate-single-file — Validate a Markdown file from the command line (task)
- t_read-validation-report — Read and act on a validation report (task) ← NEW
- t_validate-directory — Validate a directory of Markdown files (task)
- t_set-output-format — Set the output format for validation reports (task)
- t_save-reports — Save validation reports to a directory (task)
- t_integrate-github-actions — Add markdown-validator to a GitHub Actions workflow (task)

**Reference:**
- r_cli-options — CLI options and flags reference (reference)
- r_exit-codes — Exit codes reference (reference)
- r_report-output — Validation report output format reference (reference)

### Rule Creator Guide
**Concepts:**
- c_rule-sets-overview — Understanding rule sets (concept)
- c_rule-anatomy — Anatomy of a validation rule (concept)
- c_workflow-language-overview — Understanding the workflow step language (concept) ← EXPANDED
- c_rule-design-patterns — Rule design patterns for common editorial checks (concept) ← NEW
- c_rule-governance — Rule set governance and versioning (concept) ← EXPANDED
- c_known-limitations — Known limitations of markdown-validator (concept) ← NEW

**Tasks:**
- t_create-rule-set — Create a rule set file (task)
- t_write-header-rule — Write a header rule to check front-matter metadata (task)
- t_write-body-rule — Write a body rule to check document structure (task)
- t_write-workflow — Write a workflow for conditional rule chains (task)
- t_start-repl — Start the interactive REPL (task)
- t_test-rule-repl — Test a rule in the interactive REPL (task)
- t_test-workflow-repl — Test a workflow in the interactive REPL (task) ← NEW
- t_deploy-rule-set — Deploy and version a rule set (task) ← EXPANDED

**Reference:**
- r_rule-fields — Rule fields reference (reference)
- r_flags — Flags reference with examples (reference)
- r_operators — Operators reference with examples (reference)
- r_workflow-steps — Workflow step patterns reference (reference)
- r_repl-commands — REPL commands reference (reference)

### Troubleshooting
- ts_nltk-error — Resolve a NLTK LookupError on first run (troubleshooting)
- ts_no-frontmatter — Resolve a ParseError caused by missing front matter (troubleshooting)
- ts_rule-never-passes — Debug a rule that never passes on a valid document (troubleshooting)
- ts_xpath-wrong-results — Debug an XPath expression that returns unexpected results (troubleshooting)
- ts_ci-fails — Resolve a validation failure in a CI/CD pipeline (troubleshooting)

### Shared
- glossary — Glossary of markdown-validator terms (glossary)

---

## 4. Topic Type Map

| File | DITA type | Audience |
|---|---|---|
| c_what-is-markdown-validator | concept | user, rule-creator |
| c_how-validation-works | concept | user, rule-creator |
| c_validation-levels | concept | user, rule-creator |
| c_ci-integration-overview | concept | user |
| t_install | task | user |
| t_download-nltk | task | user |
| t_validate-single-file | task | user |
| t_read-validation-report | task | user |
| t_validate-directory | task | user |
| t_set-output-format | task | user |
| t_save-reports | task | user |
| t_integrate-github-actions | task | user |
| r_cli-options | reference | user, rule-creator |
| r_exit-codes | reference | user |
| r_report-output | reference | user |
| c_rule-sets-overview | concept | rule-creator |
| c_rule-anatomy | concept | rule-creator |
| c_workflow-language-overview | concept | rule-creator |
| c_rule-design-patterns | concept | rule-creator |
| c_rule-governance | concept | rule-creator |
| c_known-limitations | concept | rule-creator |
| t_create-rule-set | task | rule-creator |
| t_write-header-rule | task | rule-creator |
| t_write-body-rule | task | rule-creator |
| t_write-workflow | task | rule-creator |
| t_start-repl | task | rule-creator |
| t_test-rule-repl | task | rule-creator |
| t_test-workflow-repl | task | rule-creator |
| t_deploy-rule-set | task | rule-creator |
| r_rule-fields | reference | rule-creator |
| r_flags | reference | rule-creator |
| r_operators | reference | rule-creator |
| r_workflow-steps | reference | rule-creator |
| r_repl-commands | reference | rule-creator |
| ts_nltk-error | troubleshooting | user, rule-creator |
| ts_no-frontmatter | troubleshooting | user |
| ts_rule-never-passes | troubleshooting | rule-creator |
| ts_xpath-wrong-results | troubleshooting | rule-creator |
| ts_ci-fails | troubleshooting | user |
| glossary | glossentry (group) | user, rule-creator |

Total: 39 content files + 3 DITA maps = 42 files
