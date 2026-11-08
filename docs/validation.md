# Validation and reproduction

The checks compare the implementation with independently specified mathematical
facts. They do not use agreement between two copies of the same iteration code
as the primary oracle.

| Check | Reference |
|---|---|
| Simple Liar | Exact involution `f(f(x))=x`, fixed point and two-cycles |
| k-Sayer | Exact closed form `x* + (-(1-k))^n (x0-x*)`, including both parameter boundaries |
| Scalar model formulas | The unsimplified self-attribution operator on a rational grid |
| Chaotic Liar | Both twenty-step sequences on printed p. 671 of Mar & Grim |
| Minimalist / Half-Sayer | Exactly stationary `2/3`; perturbation factors `-2` and `-1/2` |
| Curry | The `p=0` and `p=1` algebraic reductions; the interior period-two example |
| Coupled rules | Hand-calculated first sweeps, the published dyadic trajectory, a rational four-cycle, and the simultaneous triangle constraint |
| Arithmetic | Type/range preservation, floating collapse versus the exact tent orbit |
| Diagnostics | Positive expansion on a periodic orbit, undefined derivatives at corners, zero derivative status |
| Exports / CLI | Replay from JSON settings, exact fractions retained, CSV agreement, plotting and invalid inputs |

`float32` and `float64` use NumPy scalar arithmetic at every update. Rational
runs use Python's `Fraction`; a float is rejected as an exact-mode input because
it has already lost the original decimal information. Domain validation occurs
before floating-point rounding, and trajectories are never clipped to conceal
out-of-range results.

## Run the checks

```sh
uv sync --locked --extra test --extra notebook
uv run --locked --extra test --extra notebook pytest -q
uv run --locked --extra test --extra notebook ruff check .
uv run --locked --extra test --extra notebook python examples/reproduce.py --out scratch/reproduced
uv run --locked --extra test --extra notebook python examples/execute_notebook.py --output scratch/paradox_lab.ipynb
```

The workflow in [CI](../.github/workflows/ci.yml) runs these commands on Python
3.12 and 3.13 and uploads fresh figures, trajectories and an executed notebook.
Notebook execution uses the selected environment's interpreter. The repository
also commits a complete executed notebook for readers who do not install Python.

## Provenance and limits

Each trajectory records all states and requested settings. Its JSON includes
source-file SHA-256 hashes, package versions, source-page locations, represented
inputs, and hexadecimal initial binary values where relevant. The summary also
hashes the figure-generation script. Compare numerical fields when reproducing
on another machine; Python versions and PNG metadata can differ.

Recurrence detection uses exact equality in the selected representation and
checks the entire state vector. It does not use a tolerance that could confuse
nearby states with a true repeat. Failure to find a repeat within a finite run is
reported as absence of a detected recurrence, not evidence of chaos.

The scalar tangent diagnostic differentiates the ideal equation on its branches,
not the discontinuous rounding operation. A corner produces an explicit undefined
status. A zero derivative produces a negative-infinity status with a JSON `null`
value, keeping the export valid JSON. We do not estimate Lyapunov spectra or
fractal dimensions for the coupled maps in this release.
