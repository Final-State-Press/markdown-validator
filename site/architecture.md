# Architecture

## Layer diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  CLI  (markdown_validator.cli)                                      │
│  Click batch validator + interactive cmd.Cmd REPL                   │
└───────────────────────────┬─────────────────────────────────────────┘
                            │  calls
┌───────────────────────────▼─────────────────────────────────────────┐
│  Services  (markdown_validator.services)                            │
│  Scanner (Facade) · WorkflowEngine (Chain of Responsibility)        │
└──────────┬───────────────────────────────────┬──────────────────────┘
           │  uses                             │  uses
┌──────────▼──────────┐            ┌───────────▼───────────────────────┐
│  Infrastructure     │            │  Domain                           │
│  parser.py          │            │  models.py  (Value Objects)       │
│  loader.py          │            │  operators.py  (Strategy)         │
│  reporter.py        │            │  evaluator.py                     │
│                     │            │  pos.py                           │
└─────────────────────┘            └───────────────────────────────────┘
```

**Dependency rule**: each layer may only depend on layers to its right.
The CLI never calls infrastructure directly.

## Module responsibilities

See [DESIGN.md](../DESIGN.md) for the full responsibility matrix and design pattern justifications.

## Data flow

```
.md file ──► parser.py ──► ParsedDocument (frozen)
                                │
rules.json ──► loader.py ──► RuleSetModel (frozen)
                                │
               evaluator.py ◄───┘
                    │
               ValidationResult (per rule, frozen)
                    │
               ScanReport (aggregated, frozen)
                    │
               reporter.py ──► report.json / report.csv
```
