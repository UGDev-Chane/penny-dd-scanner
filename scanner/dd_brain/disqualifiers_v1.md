# Disqualifiers v1 (Hard Gates)

These rules override any numeric score. If a disqualifier triggers, the default output is **PASS** unless explicitly labeled as **SPECULATIVE**.

## Hard Pass (Default)

1. **Going Concern Flag = YES**
   - Any explicit “substantial doubt about our ability to continue as a going concern” language in filings.

2. **Delisting or Noncompliance**
   - Exchange notice, late filings, repeated compliance extensions, or clear risk of delisting.

3. **Liquidity Trap**
   - Average daily dollar volume is too low to enter and exit without significant slippage.
   - v1 threshold suggestion: **< $1M avg daily $ volume**.

4. **Serial Dilution Pattern**
   - Clear repeated equity issuance with no credible path to self-funding.
   - Signals: multiple offerings/ATMs in short windows, rapid shares outstanding growth.

5. **Recent Reverse Split (High Risk)**
   - Reverse split within last **24 months**.
   - Default to PASS unless there is a strong turnaround narrative and dilution has stopped.

## Speculative Allowed (Must Be Labeled)

Allowed only if the watchlist status is explicitly **SPECULATIVE**:

- Going concern is close but not officially flagged.
- One-time capital raise with clear runway and execution proof.
- Extreme volatility / catalysts that are clearly time-bounded.

## Notes

- Disqualifiers exist to protect against “high score, low survivability” situations.
- When a disqualifier triggers, the DD memo must explicitly name it and explain why.
