"""Iteration, exact recurrence detection, diagnostics, and portable exports."""

import csv
import hashlib
import json
import math
import platform
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np

from .models import MODELS, pair_component, scalar_derivative, scalar_value

PRECISIONS = {"float32": np.float32, "float64": np.float64, "rational": Fraction}
SCHEDULES = ("simultaneous", "x-then-y", "y-then-x")
SOURCE_URL = "https://pgrim.org/articles/patternandchaos.pdf"


def _number(value, precision):
    if precision == "rational" and isinstance(value, (float, np.floating)):
        raise ValueError("Use strings, integers, or Fraction values for exact rational inputs")
    # Validate before rounding, which could otherwise hide out-of-domain inputs.
    exact = Fraction(value) if precision == "rational" else Fraction(str(value))
    if not 0 <= exact <= 1:
        raise ValueError("Initial values and parameters must lie in [0, 1]")
    return exact if precision == "rational" else PRECISIONS[precision](float(exact))


def _log_abs(value):
    if isinstance(value, Fraction):
        return math.log(abs(value.numerator)) - math.log(value.denominator)
    return math.log(abs(float(value)))


def recurrence(states):
    """First exactly repeated stored state; no tolerance-based chaos classifier."""
    seen = {}
    for t, state in enumerate(states):
        if state in seen:
            return {"start": seen[state], "period": t - seen[state], "first_repeat": t}
        seen[state] = t
    return None


@dataclass
class Trajectory:
    model: str
    precision: str
    schedule: str
    parameters: dict
    states: list[tuple]
    requested_initial: list[str]
    requested_parameters: dict[str, str]

    def array(self):
        """Float64 view for plotting only; exact arithmetic stays in states."""
        return np.array([[float(v) for v in state] for state in self.states])

    def diagnostics(self):
        cycle = recurrence(self.states)
        result = {
            "recurrence": cycle,
            "recurrence_meaning": (
                "Exact recurrence for this rational initial state"
                if self.precision == "rational"
                else "Exact recurrence of stored floating-point states only"
            ),
            "tangent_log_gain": None,
        }
        if MODELS[self.model].dimension == 1 and len(self.states) > 1:
            slopes = [
                scalar_derivative(self.model, s[0], self.parameters) for s in self.states[:-1]
            ]
            if any(s is None for s in slopes):
                gain = {"value": None, "status": "undefined_at_corner"}
            elif any(s == 0 for s in slopes):
                gain = {"value": None, "status": "negative_infinity_zero_derivative"}
            else:
                gain = {
                    "value": float(np.mean([_log_abs(s) for s in slopes])),
                    "status": "finite",
                }
            gain.update(
                samples=len(slopes),
                units="natural-log units per iteration",
                interpretation="Finite-time derivative growth of the real equation; "
                "not a test for chaos or a derivative of rounded arithmetic",
            )
            result["tangent_log_gain"] = gain
        return result

    def report(self):
        model = MODELS[self.model]
        source_hashes = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))
        }
        return {
            "schema_version": 1,
            "software": {
                "package": "paradox-dynamics",
                "version": "0.1.0",
                "python": platform.python_version(),
                "numpy": np.__version__,
                "source_sha256": source_hashes,
            },
            "model": self.model,
            "title": model.title,
            "equation": model.equation,
            "source": {"url": SOURCE_URL, "journal_pages": model.pages},
            "precision": self.precision,
            "update_schedule": self.schedule,
            "schedule_definition": (
                "All components use the previous state"
                if self.schedule == "simultaneous"
                else "One full sweep per row; the second update uses the first update's new value"
            ),
            "steps": len(self.states) - 1,
            "requested_initial": self.requested_initial,
            "requested_parameters": self.requested_parameters,
            "represented_initial": [str(v) for v in self.states[0]],
            "represented_parameters": {k: str(v) for k, v in self.parameters.items()},
            "float_initial_hex": (
                [float(v).hex() for v in self.states[0]] if self.precision != "rational" else None
            ),
            "float_parameters_hex": (
                {k: float(v).hex() for k, v in self.parameters.items()}
                if self.precision != "rational"
                else None
            ),
            "state_encoding": "rational p/q strings"
            if self.precision == "rational"
            else "JSON numbers preserving the stored binary values",
            "states": [
                [str(v) if self.precision == "rational" else float(v) for v in state]
                for state in self.states
            ],
            "diagnostics": self.diagnostics(),
        }

    def save(self, directory):
        """Write JSON provenance and CSV; rational values remain fractions in both."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "trajectory.json").write_text(
            json.dumps(self.report(), indent=2, allow_nan=False) + "\n"
        )
        names = ["x", "y"][: MODELS[self.model].dimension]
        with (directory / "trajectory.csv").open("w", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["iteration", *names])
            writer.writerows(
                (t, *(str(v) if self.precision == "rational" else float(v) for v in state))
                for t, state in enumerate(self.states)
            )


def simulate(
    model, initial, *, steps=100, precision="float64", schedule="simultaneous", parameters=None
):
    """Run a map. Supply rational inputs as decimal/fraction strings, not floats.

    A coupled step is a full sweep. In sequential schedules the second update
    sees the first update immediately. Scalar schedules must be simultaneous.
    """
    if model not in MODELS:
        raise ValueError(f"Unknown model {model!r}; choose from {', '.join(MODELS)}")
    if precision not in PRECISIONS:
        raise ValueError(f"Unknown precision {precision!r}")
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    if schedule not in SCHEDULES:
        raise ValueError(f"Unknown schedule {schedule!r}")
    spec = MODELS[model]
    if spec.dimension == 1 and schedule != "simultaneous":
        raise ValueError("Sequential update schedules apply only to coupled maps")
    if isinstance(initial, (str, int, float, Fraction, np.number)):
        initial = [initial]
    initial = list(initial)
    if len(initial) != spec.dimension:
        raise ValueError(f"{model} requires {spec.dimension} initial value(s)")
    requested = dict(parameters or {})
    allowed = {spec.parameter} if spec.parameter else set()
    if set(requested) - allowed:
        raise ValueError(f"Unexpected parameters: {sorted(set(requested) - allowed)}")
    if spec.parameter:
        requested.setdefault(spec.parameter, spec.default)
    params = {key: _number(value, precision) for key, value in requested.items()}
    states = [tuple(_number(v, precision) for v in initial)]
    cast = PRECISIONS[precision]
    for _ in range(steps):
        old = states[-1]
        if spec.dimension == 1:
            new = (cast(scalar_value(model, old[0], params)),)
        elif schedule == "simultaneous":
            new = tuple(cast(pair_component(model, i, old)) for i in (0, 1))
        else:
            new = list(old)
            for i in (0, 1) if schedule == "x-then-y" else (1, 0):
                new[i] = cast(pair_component(model, i, new))
            new = tuple(new)
        if any(not 0 <= v <= 1 for v in new):
            raise ArithmeticError("Map left [0,1]; values are never silently clipped")
        states.append(new)
    return Trajectory(
        model,
        precision,
        schedule,
        params,
        states,
        list(map(str, initial)),
        {k: str(v) for k, v in requested.items()},
    )
