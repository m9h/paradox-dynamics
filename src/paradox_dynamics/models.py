"""Equations from Mar & Grim (1991); page numbers are printed journal pages.

All operations preserve Fraction / numpy float32 / numpy float64 arithmetic.
The piecewise tent evaluation avoids cancellation near zero. Algebraically
equivalent expressions need not have identical floating-point trajectories.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    title: str
    dimension: int
    equation: str
    pages: str
    parameter: str | None = None
    default: str | None = None


MODELS = {
    "liar": Model("Simple Liar", 1, "x' = 1 - x", "662–664"),
    "truth-teller": Model("Truth-Teller", 1, "x' = x", "667"),
    "samesayer": Model("Samesayer", 1, "x' = 1", "667–668"),
    "k-sayer": Model("k-Sayer", 1, "x' = 1 - (1-k)*x", "668–669", "k", "0.5"),
    "minimalist": Model("Minimalist", 1, "x' = 1 - abs(min(x,1-x)-x)", "665–666"),
    "chaotic-liar": Model("Chaotic Liar", 1, "x' = 1 - abs(1-2*x)", "670–672"),
    "curry": Model("Curry variation", 1, "x' = 1 - abs(max(1-x,p)-x)", "674–676", "p", "0.75"),
    "dualist": Model("Simple Dualist", 2, "x' = 1-y; y' = x", "676–677"),
    "dual-revision": Model(
        "Dualist value-revision pair",
        2,
        "x' = 1-abs(y-x); y' = 1-abs((1-x)-y)",
        "677–679",
    ),
}


def scalar_value(name, x, parameters):
    one = type(x)(1)
    two = type(x)(2)
    if name == "liar":
        return one - x
    if name == "truth-teller":
        return x
    if name == "samesayer":
        return one
    if name == "k-sayer":
        return one - (one - parameters["k"]) * x
    if name == "minimalist":
        return one if x <= one / two else two * (one - x)
    if name == "chaotic-liar":
        return two * x if x <= one / two else two * (one - x)
    if name == "curry":
        return one - abs(max(one - x, parameters["p"]) - x)
    raise ValueError(f"Not a scalar map: {name}")


def pair_component(name, index, state):
    x, y = state
    one = type(x)(1)
    if name == "dualist":
        return one - y if index == 0 else x
    if name == "dual-revision":
        return one - abs(y - x) if index == 0 else one - abs((one - x) - y)
    raise ValueError(f"Not a coupled map: {name}")


def scalar_derivative(name, x, parameters):
    """Derivative on a branch; None at a corner (conservative at boundaries).

    This differentiates the real-valued equation, not IEEE rounding. A positive
    derivative-based expansion rate is also possible on a repelling periodic orbit.
    """
    one = type(x)(1)
    two = type(x)(2)
    if name == "liar":
        return -1
    if name == "truth-teller":
        return 1
    if name == "samesayer":
        return 0
    if name == "k-sayer":
        return -(one - parameters["k"])
    if name in ("minimalist", "chaotic-liar"):
        if x == one / two:
            return None
        if x > one / two:
            return -2
        return 0 if name == "minimalist" else 2
    if name == "curry":
        p = parameters["p"]
        if p == 1:
            return 1  # This boundary case is the identity, not a constant map.
        if p == 0:
            return scalar_derivative("chaotic-liar", x, {})
        if x == one - p:
            return None
        h = max(one - x, p) - x
        if h == 0:
            return None
        magnitude = 2 if x < one - p else 1
        return magnitude if h > 0 else -magnitude
    raise ValueError(f"Not a scalar map: {name}")
