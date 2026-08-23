# Analysis plan

This plan is fixed before the full benchmark is run.

## Scope

Maia 2 is evaluated only as its intended book-enabled configuration. Family
comparisons therefore compare book-enabled Maia 2 with book-enabled Maia 3;
they do not estimate a Maia 2 no-book effect. Maia 3 book effects are estimated
within Maia 3.

## Primary comparisons

1. Maia 2 versus Maia 3 at the same rating in book-enabled configurations.
2. Maia 3 book versus no-book at the same rating and sampling policy.
3. Maia 3 argmax, balanced, and maximum-sampling policies at the same rating
   and book condition.

Opening-pair clustered intervals are primary. The report will distinguish
pre-registered primary contrasts from exploratory round-robin comparisons.

## Outcomes

The primary outcome is score percentage: win = 1, draw = 0.5, loss = 0.
Games reaching the maximum ply limit are draws. A sensitivity result excludes
those cutoffs. Genuine engine failures are unresolved and never silently
entered into W/D/L.

The final analysis will also include a coherent all-profile rating model, with
uncertainty bootstrapped over opening IDs, and multiplicity-adjusted exploratory
comparisons. The exact model implementation will be reviewed before the full
run; pairwise raw counts remain the authoritative input.
