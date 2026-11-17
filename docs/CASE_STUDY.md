# Case-study approach

## 1. Define the accounting grain before calculating payouts

Map operational and billing identifiers to one CRM account. Select the earliest qualifying activation rather than letting a later opportunity restart an account. Aggregate once at account level before joining to representatives. A repeated opportunity row is not a second source of operational revenue.

## 2. Keep recognition, attribution and payment separate

Recognition asks when activity qualifies. Attribution asks which representative or management chain receives credit. Payment applies employment eligibility, guarantees, payout rates and accelerators. Treating these as one opaque spreadsheet formula obscures why a number changed.

## 3. Make policy decisions visible

The model distinguishes posted from worked activity, approved from denied billing credits, and marginal accelerator tiers from whole-amount multipliers. It supports isolated counterfactuals for alternate interpretations. These are analytical sensitivities, not approvals to withhold or release payment. Date anchors and partial employment need explicit business-policy decisions rather than convenient defaults.

## 4. Preserve an audit trail

Account summaries, recognition events and representative totals are separate exports. Events retain source-row references, while the detailed activity trace retains the individual activity ID. This makes a disputed payout traceable without relying solely on a total-level tie-out.

## 5. Test both numbers and failure paths

The public test suite independently hand-calculates the fictional representative payouts, reconciles event credit to accounts, checks ramp and FX arithmetic, and exercises duplicate-opportunity, denied-credit, posted/worked and window-boundary cases. It also checks duplicate source-key rejection, missing future-month data and refusal to overwrite a prior run.

These tests validate the public example only. They do not establish that the original assessment workbook, the full original refresh system, or any real payroll has passed new testing.

## Practical lessons

- Good data lineage can be more useful than a more elaborate dashboard.
- A “correct” formula can still implement the wrong business rule.
- Independent checks should reconstruct arithmetic, not merely compare the engine with itself.
- A scenario delta is conditional; overlapping scenario deltas should not be summed indiscriminately.
- Preserve both literal entitlement and unresolved policy questions instead of hiding uncertainty in a single recommended payment.

## Original conclusions versus demonstration

This document summarizes the analytical approach. It deliberately does not reproduce the original employer-specific numerical findings, entity names or recruiting task. The public results are new synthetic calculations and should never be quoted as original Clipboard Health results.
