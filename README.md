# Sales Compensation Analytics
### From fragmented operational exports to an auditable commission model

A portfolio adaptation of Charlie Nie's Clipboard Health sales-compensation case study. Built around account-level attribution, revenue-recognition windows, ramp guarantees, marginal accelerators, manager rollups, and reconciliation controls.

> **Public synthetic edition.** Every input row and every numerical result in this repository is newly generated fictional demonstration data. These are **not** the original case-study results, employee records, or Clipboard Health compensation policies. This repository is not affiliated with or endorsed by Clipboard Health.

## Start here

- [Case-study approach and decisions](docs/CASE_STUDY.md)
- [Verified synthetic results](outputs/REPORT.md)
- [Calculation engine](src/calculate.py)
- [11 automated checks](tests/test_demo.py)
- [Data provenance and publication boundary](docs/DATA_PROVENANCE.md)

## The analytical problem

Sales compensation connects CRM opportunities, operational activity, billing credits, HR employment dates, and compensation plans. A plausible total is not enough: each dollar needs a defensible recognition rule, owner, and source trail. Duplicate opportunity joins, conflicting date anchors, or incorrectly applied accelerator tiers can create systematic overpayment or underpayment.

This project separates **reconstructed entitlement** from **cash actually paid**, makes ambiguous rules explicit, and tests alternative interpretations without treating all scenario deltas as additive.

## Reproduce in under a minute

Python 3.10+; no third-party packages, credentials, network, or spreadsheet application required for this public demo.

```bash
python3 run_demo.py --output runs/demo
python3 -m unittest discover -s tests -v
```

Use a new output directory for each run. The runner refuses to overwrite earlier runs. `generate_demo.py` builds independent fictional inputs; it never opens the original assessment files.

Each run produces JSON and CSV files for account calculations, credited events, representative payouts and source-row traces, plus a concise Markdown report. The committed `outputs/` files were produced by an actual run of this demo.

## Demonstrated results (synthetic only)

| Metric | Result |
|---|---:|
| Fictional representatives | 5 |
| Fictional accounts | 4 |
| Activity rows | 105 |
| Current-plan total | $1,164.80 |
| Repriced total | $1,046.30 |
| Isolated repricing difference | −$118.50 |

The scenario changes SMB AE marginal tier multipliers to 1.3× and 1.5×. It is an illustrative what-if, not a recommendation for a real employer. See the report for individual payouts and the tests for hand-calculated expected values.

## Model capabilities

- Stable account mapping across opportunity, activity and billing exports
- Earliest qualifying Closed Won activation and account-level deduplication
- 30/60/90-day credit windows and incremental later-window recognition
- Posted versus worked activity distinction for different account types
- Approved billing credits, existing-book revenue and retention incentives
- Day-level employment eligibility and prorated ramp guarantees
- Marginal accelerator bands, isolated repricing, hierarchical rollups and FX
- Source-row traces, reconciliation controls, failure on duplicate keys and incomplete future-month data

## What is preserved from the original project?

The public calculation engine is adapted from the final November 11 submission-review version. Its calculation logic is retained; the runner, fictional data, public documentation and test fixtures are new. Input provenance paths were changed from XLSX to JSON for this dependency-free edition. The original broader workbook-generation and source-contract refresh pipeline remains in a separate private archive; **this demo does not reproduce or validate that complete pipeline**.

## Limitations

This is a bounded case-study model, not production payroll software. It is not an effective-dated ownership engine, it cannot establish that an extract is complete, and it cannot approve compensation policy. Partial-month AM handling in the engine is provisional and not exercised by the demo; do not use it without an approved policy. Manager hierarchy cycles fail instead of being silently accepted. The public example is for June 2026 only, not a general live-data refresh system. CSV/JSON outputs are not the original formula workbook, and no native Excel/LibreOffice validation is claimed for this edition.

## Publication scope

The employer-provided prompt, source data, recruiter communications, original model/report and original validation artifacts are intentionally not distributed here because public redistribution permission has not been established. The complete original submission-review project is preserved separately in the owner's **private** archive. No license for employer material is granted or implied by this repository.

Author: **Charlie Nie**
