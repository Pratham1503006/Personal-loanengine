# Research Methodology

All current sources were accessed on **2026-10-11**; the access date is recorded per
source in `data/source_registry.csv`.

## Search order

1. **Official lender pages first** — product page, eligibility page, interest-rates &
   charges page, calculator, FAQs, terms.
2. **Official product documents/PDFs** linked from official pages.
3. **RBI material** for regulatory context only. General RBI requirements are never
   recorded as lender-specific underwriting rules.
4. **Reputable comparison sites** used only as discovery/cross-check; any rule found only
   there is labelled `verified_secondary` at most.
5. Search snippets are never the sole evidence when the actual page can be opened.
   Logins, paywalls and anti-bot controls are not bypassed.

## Evidence quality & status vocabulary

- `verified_official` — directly supported by a current official lender/regulatory source.
- `verified_secondary` — credible secondary source only; never treated as a verified hard
  gate by the engine.
- `estimated` — model assumption inferred from documented evidence; always carries an
  `assumption_description`; never presented as official policy.
- `not_published` — researched but no reliable public threshold found; values stored as
  null (never zero).
- `not_researched` — research not yet completed.
- `unverified` — a source/value exists but could not be validated.
- `stale` — currency uncertain.

## Rule interpretation

- Each rule is one row in `data/lender_rules.csv` with parameter, operator, segment scope
  (`salaried` / `self_employed` / `all`), product name, and mandatory flag.
- Salaried criteria are never applied to self-employed applicants unless the source says so.
- Conflicting sources: the official source wins; the conflict is noted in `notes`.
- Unknown or unpublished thresholds remain null with matching evidence status; the engine
  yields `REVIEW_REQUIRED` rather than silently passing a gate.

## Research gaps recorded

- Applicant-specific pricing and income-based maximum-loan formulas (often discretionary,
  unpublished) are marked `not_published` / `NOT_PUBLICLY_DETERMINABLE`.
- Self-employed income criteria are largely unpublished for many lenders.
- Digital platforms (Moneyview) show partner-lender criteria; the regulated funding
  entity is recorded per row instead of implying platform underwriting.
