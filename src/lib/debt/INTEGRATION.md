# Calculation and integration notes

The original uploaded `dept4.py` is preserved as `original_engine.py`. The deployed website cannot execute Python/pandas, so `engine.ts` adapts its simulation directly with decimal.js rounding, interest formulas, strategy ordering and payment rollover. Tests compare full-term monthly-standard outputs with the actual original Python engine: avalanche 14 months / 680.49 interest; snowball 15 months / 806.96 interest for the test fixture.

The adaptation fixes the original safety-buffer omission: contributions to reserves and savings are deducted before repayment capacity. Unknown values block estimation, and infeasible budgets cannot activate a plan. Dates clamp due days to the actual month length. Monthly/daily/flat interest estimates are disclosed in the plan page. Fees and lender-specific contracts are not modeled.

Payments are manual confirmations. The confirmed schedule supplies a single interest estimate per debt per payment month, with all subsequent partial payments avoiding double interest. Balances and projections update without replacing prior plans. This approximation is not a bank-verified ledger; missed-period interest/fees require reviewing the actual balance with the lender.

Cloud stores private workspace state behind owner-only RLS. Fictional sample mode is separate and browser-only. Google and Lovable sign-in providers are enabled. Signed-in storage remains unverified end-to-end because there were no auth users available for a test session.

ElevenLabs integration source, Custom Voice ID and private API key were not supplied. Voice controls explicitly show this unavailable state and never collect recordings or claim speech generation. When provided, implement transcription and TTS in authenticated TanStack server functions; do not expose secrets to the browser. Review extracted values before saving. Use confirmed plan data for every spoken financial figure.

There is no connected AI adviser. Recommendations use the user's stated preference and deterministic calculation comparisons, disclosed in the strategy page. Only visible in-app reminders are implemented; no email, push, SMS or bank payment initiation is connected.