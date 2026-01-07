# AGENTS.md

## Role of the System
This system is a **decision-support tool**, not an autonomous trader.

It surfaces candidates, risk context, and structured reasoning.
All final decisions are made by a human.

## Core Principles
- Hope is not a strategy
- No single signal is sufficient
- Price action has priority over narrative
- Risk is defined before reward
- Losses are acceptable. Unbounded losses are not.

## Explicit Non-Goals
- This system does NOT predict certainty
- This system does NOT optimize for win-rate
- This system does NOT execute trades
- This system does NOT override stops or risk rules

## Risk Discipline
- Every recommendation must include:
  - Clear invalidation level
  - Defined downside
  - Reason the trade should be exited if wrong
- If invalidation is unclear, no recommendation is produced.

## Human-in-the-Loop Requirement
All outputs are advisory.
Human judgment is mandatory before action.

If a human cannot explain *why* a recommendation exists,
the recommendation is considered invalid.

## Failure Memory
Past failures must inform future filters.
Patterns that caused large drawdowns must be explicitly guarded against.