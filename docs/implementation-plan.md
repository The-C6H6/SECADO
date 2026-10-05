# Modular drying implementation

Authorized scope: separate Flet, math, geometry, conversions and IP PsychroLib.
No final commit until user review. Worktree: `feat/modular-drying`.

## Modules

`units.py`, `validation.py`, `moisture.py`, `geometry.py`, `correlations.py`,
`psychrometrics.py`, `dryers/continuous.py`, `dryers/rotary.py`, `ui/app.py`.
Internal moisture is mass water / mass dry solid. Empirical constants stay unchanged.
The user subsequently confirmed h in W/(m² K), G in kg/(m² h) and dp in m;
drying times now use kg, J/kg, K and m² to return seconds, plus hours for trays.

## Tasks

1. Write failing pytest tests for conversions, balances, geometry, Reynolds and
   physical limits; implement core modules and run tests.
2. Write failing tests for IP psychrometrics, continuous profiles and defined rotary
   primitives; implement and run tests. Dependent pairs must fail explicitly.
3. Write failing tests for Flet form callbacks; implement responsive forms, result
   tables, Markdown procedures and explicit unit notices.
4. Document units and ambiguities; run full tests, compilation and independent review.

## Review focus

Nonfinite input; hidden psychrometric clamping; exact fractional and integer profile
endpoints; zero-length denominators; explicit latent heat conversion for drying time.

## Verification provenance

The user supplied both complete academic exercises, now encoded in
`tests/test_tray_time.py`, with explicitly approved 1% time and ±0.5 °F wet-bulb
tolerances. Computed times are 3.007433 h and 252.972991 s. Analytic fixtures and
physical consistency tests remain separately identified.

## Execution record

- Core tests failed on absent modules, then 49 passed.
- Psychrometrics/dryers tests failed on absent modules. Fixed identity temperature
  conversion after exact endpoint tests exposed floating-point drift. Corrected a
  synthetic test arithmetic mistake (heat input 250940, not 251000 Btu/h).
- 78 tests passed, then forms and confirmed rotary heat balance were added via
  failing tests; 98 passed.
- New dimensional confirmation replaced blocked-time assertions with SI time
  assertions. 110 passed, two academic full-exercise comparisons explicitly skipped.
- Complete academic inputs and tolerance approval received; 114 tests passed without skips.
- Desktop/web extras explicitly authorized, installed and locked with uv.
- Independent review found saturation inversion errors. Regression first: seven
  saturated pair cases failed. Fixed convergence and exact saturation boundary;
  151 tests now pass, including a test preserving real supersaturation rejection.
- Updated docs and persistent notes after source inputs and approvals arrived.
- Flet HTTP root, bootstrap and cylinder asset return 200. Browser inspection
  unavailable: no browser connected. No commits made.
