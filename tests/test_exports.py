import csv
import json
from fractions import Fraction

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from paradox_dynamics import simulate
from paradox_dynamics.cli import main
from paradox_dynamics.plotting import plot_trajectory


@pytest.mark.parametrize("precision", ["float32", "float64", "rational"])
def test_export_and_replay(tmp_path, precision):
    run = simulate(
        "dual-revision", ["0.1", "0.9"], steps=30, precision=precision, schedule="x-then-y"
    )
    run.save(tmp_path)
    report = json.loads((tmp_path / "trajectory.json").read_text())
    replay = simulate(
        report["model"],
        report["requested_initial"],
        steps=report["steps"],
        precision=report["precision"],
        schedule=report["update_schedule"],
        parameters=report["requested_parameters"],
    )
    assert replay.states == run.states
    assert report["software"]["source_sha256"]["models.py"]
    decoded = [
        tuple(Fraction(v) if precision == "rational" else float(v) for v in row)
        for row in report["states"]
    ]
    assert decoded == run.states
    rows = list(csv.reader((tmp_path / "trajectory.csv").open()))
    assert rows[0] == ["iteration", "x", "y"]
    assert len(rows) == 32
    csv_states = [
        tuple(Fraction(v) if precision == "rational" else float(v) for v in row[1:])
        for row in rows[1:]
    ]
    assert csv_states == run.states


def test_cli_exact_plot(tmp_path):
    main(
        [
            "simulate",
            "chaotic-liar",
            "--initial",
            "157/500",
            "--steps",
            "20",
            "--precision",
            "rational",
            "--out",
            str(tmp_path),
            "--plot",
        ]
    )
    assert (tmp_path / "trajectory.png").stat().st_size > 1000
    data = json.loads((tmp_path / "trajectory.json").read_text())
    assert data["represented_initial"] == ["157/500"]
    assert data["states"][1] == ["157/250"]


def test_cli_reports_bad_parameter(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["simulate", "liar", "--initial", "0.2", "--parameter", "0.5", "--out", str(tmp_path)])
    assert error.value.code == 2


@pytest.mark.parametrize("model,initial", [("liar", "1/4"), ("dual-revision", ["1/4", "1/8"])])
def test_plotting_keeps_exact_states(model, initial):
    run = simulate(model, initial, steps=10, precision="rational")
    original = list(run.states)
    figure = plot_trajectory(run)
    figure.canvas.draw()
    assert run.states == original
    assert all(isinstance(v, Fraction) for state in run.states for v in state)
    plt.close(figure)
