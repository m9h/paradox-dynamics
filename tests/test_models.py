import math
from fractions import Fraction as Q

import numpy as np
import pytest

from paradox_dynamics import MODELS, simulate
from paradox_dynamics.models import scalar_value


@pytest.mark.parametrize("start", ["0", "1/8", "1/3", "1/2", "1"])
def test_liar_exact_involution(start):
    run = simulate("liar", start, steps=30, precision="rational")
    x = Q(start)
    assert [row[0] for row in run.states] == [x if n % 2 == 0 else 1 - x for n in range(31)]
    assert run.diagnostics()["recurrence"]["period"] == (1 if x == Q(1, 2) else 2)


@pytest.mark.parametrize("k", ["0", "1/4", "1/2", "3/4", "1"])
def test_k_sayer_closed_form(k):
    run = simulate("k-sayer", "3/7", parameters={"k": k}, steps=50, precision="rational")
    a = 1 - Q(k)
    fixed = 1 / (2 - Q(k))
    for n, (x,) in enumerate(run.states):
        assert x == fixed + (-a) ** n * (Q(3, 7) - fixed)


@pytest.mark.parametrize("name", [name for name, spec in MODELS.items() if spec.dimension == 1])
def test_independent_semantic_operator(name):
    # Oracle is the unsimplified self-attribution schema, not the branch code.
    for x in (Q(i, 100) for i in range(101)):
        claimed = {
            "liar": Q(0),
            "truth-teller": Q(1),
            "samesayer": x,
            "k-sayer": Q(2, 7) * x,
            "minimalist": min(x, 1 - x),
            "chaotic-liar": 1 - x,
            "curry": max(1 - x, Q(3, 7)),
        }[name]
        assert scalar_value(name, x, {"k": Q(2, 7), "p": Q(3, 7)}) == 1 - abs(claimed - x)


def test_paper_tent_table_page_671():
    # Two published 20-step sequences, in exact decimal arithmetic.
    expected = {
        "0.314": [
            628,
            744,
            512,
            976,
            48,
            96,
            192,
            384,
            768,
            464,
            928,
            144,
            288,
            576,
            848,
            304,
            608,
            784,
            432,
            864,
        ],
        "0.3141": [
            6282,
            7436,
            5128,
            9744,
            512,
            1024,
            2048,
            4096,
            8192,
            3616,
            7232,
            5536,
            8928,
            2144,
            4288,
            8576,
            2848,
            5696,
            8608,
            2784,
        ],
    }
    for start, numerators in expected.items():
        denominator = 1000 if start == "0.314" else 10000
        run = simulate("chaotic-liar", start, steps=20, precision="rational")
        assert [x for (x,) in run.states[1:]] == [Q(n, denominator) for n in numerators]


def test_minimalist_repeller_and_halfsayer_attractor():
    fixed = Q(2, 3)
    for model, multiplier in [("minimalist", Q(-2)), ("k-sayer", Q(-1, 2))]:
        stable = simulate(model, fixed, steps=10, precision="rational")
        assert all(row == (fixed,) for row in stable.states)
        perturbed = simulate(model, fixed + Q(1, 100000), steps=8, precision="rational")
        assert perturbed.states[-1][0] - fixed == multiplier**8 / 100000


def test_curry_boundaries_and_paper_cycle():
    for x in [Q(i, 20) for i in range(21)]:
        assert scalar_value("curry", x, {"p": Q(0)}) == scalar_value("chaotic-liar", x, {})
        assert scalar_value("curry", x, {"p": Q(1)}) == x
    run = simulate("curry", "1/5", parameters={"p": "3/4"}, steps=12, precision="rational")
    assert set(run.states[-4:]) == {(Q(17, 20),), (Q(9, 10),)}
    assert run.diagnostics()["recurrence"]["period"] == 2


@pytest.mark.parametrize("schedule,period", [("simultaneous", 4), ("x-then-y", 2), ("y-then-x", 2)])
def test_simple_dualist_schedule(schedule, period):
    run = simulate("dualist", ["1/4", "1/8"], steps=12, precision="rational", schedule=schedule)
    assert run.diagnostics()["recurrence"]["period"] == period
    if schedule == "y-then-x":
        assert run.states[1] == (Q(3, 4), Q(1, 4))


def test_paper_dual_pair_trajectory_and_four_cycle():
    run = simulate("dual-revision", ["1/8", "1/8"], steps=8, precision="rational")
    expected = [
        (1, Q(1, 4)),
        (Q(1, 4), Q(3, 4)),
        (Q(1, 2), 1),
        (Q(1, 2), Q(1, 2)),
        (1, 1),
        (1, 0),
        (0, 1),
        (0, 1),
    ]
    assert run.states[1:] == expected
    periodic = simulate("dual-revision", ["0.4", "0.6"], steps=8, precision="rational")
    assert periodic.states[4] == periodic.states[0]
    assert periodic.diagnostics()["recurrence"]["period"] == 4


def test_coupled_sequential_uses_new_value():
    initial = ["1/5", "2/5"]
    expected = {
        "simultaneous": (Q(4, 5), Q(3, 5)),
        "x-then-y": (Q(4, 5), Q(4, 5)),
        "y-then-x": (Q(3, 5), Q(3, 5)),
    }
    for schedule, result in expected.items():
        run = simulate("dual-revision", initial, steps=1, precision="rational", schedule=schedule)
        assert run.states[1] == result


def test_simultaneous_triangle_constraint():
    for x in range(11):
        for y in range(11):
            run = simulate("dual-revision", [Q(x, 10), Q(y, 10)], steps=1, precision="rational")
            assert sum(run.states[-1]) >= 1


@pytest.mark.parametrize("precision", ["float32", "float64", "rational"])
@pytest.mark.parametrize("model", list(MODELS))
def test_range_and_arithmetic_preservation(model, precision):
    initial = ["0.314159265358979323846", "0.271828182845904523536"][: MODELS[model].dimension]
    run = simulate(model, initial, steps=120, precision=precision)
    expected_type = {"float32": np.float32, "float64": np.float64, "rational": Q}[precision]
    for state in run.states:
        for value in state:
            assert type(value) is expected_type
            assert 0 <= value <= 1


def test_precision_changes_tent_orbit():
    a = simulate("chaotic-liar", "0.314", steps=100, precision="float32")
    b = simulate("chaotic-liar", "0.314", steps=100, precision="float64")
    exact = simulate("chaotic-liar", "0.314", steps=100, precision="rational")
    assert a.states[-1] == b.states[-1] == (0,)
    assert all(x != 0 for (x,) in exact.states)
    assert a.diagnostics()["recurrence"]["start"] < b.diagnostics()["recurrence"]["start"]


def test_positive_log_gain_does_not_imply_nonperiodic_orbit():
    run = simulate("chaotic-liar", "2/3", steps=12, precision="rational")
    assert run.diagnostics()["recurrence"]["period"] == 1
    assert run.diagnostics()["tangent_log_gain"]["value"] == pytest.approx(math.log(2))


def test_corner_zero_derivative_and_no_steps():
    corner = simulate("chaotic-liar", "1/2", steps=3, precision="rational")
    assert corner.diagnostics()["tangent_log_gain"]["status"] == "undefined_at_corner"
    flat = simulate("samesayer", "0.2", steps=3)
    assert flat.diagnostics()["tangent_log_gain"]["status"] == "negative_infinity_zero_derivative"
    assert simulate("liar", "0.2", steps=0).diagnostics()["tangent_log_gain"] is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"model": "missing"},
        {"initial": "nan"},
        {"initial": "-0.1"},
        {"initial": "1.1"},
        {"steps": -1},
        {"steps": 1.5},
        {"steps": True},
        {"precision": "float16"},
        {"schedule": "random"},
        {"schedule": "x-then-y"},
        {"parameters": {"k": "0.2"}},
        {"precision": "rational", "initial": 0.1},
        {"initial": ["0.1", "0.2"]},
    ],
)
def test_invalid_configurations(kwargs):
    options = {"model": "liar", "initial": "1/4", **kwargs}
    with pytest.raises(ValueError):
        simulate(**options)


@pytest.mark.parametrize("model,parameter", [("curry", "p"), ("k-sayer", "k")])
def test_parameter_domain(model, parameter):
    with pytest.raises(ValueError):
        simulate(model, "1/4", parameters={parameter: "2"})


@pytest.mark.parametrize("precision", ["float32", "float64"])
def test_domain_validation_precedes_rounding(precision):
    with pytest.raises(ValueError):
        simulate("liar", "1.00000000000000000000000000000000001", precision=precision)


def test_tiny_rational_derivative_does_not_underflow_in_log():
    k = 1 - Q(1, 10**400)
    run = simulate("k-sayer", "1/4", parameters={"k": k}, steps=2, precision="rational")
    assert run.diagnostics()["tangent_log_gain"]["value"] == pytest.approx(-400 * math.log(10))
