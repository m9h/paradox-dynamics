"""Generate original figures, exact/floating trajectories, and a summary report.

Run from any working directory: uv run python examples/reproduce.py --out results
"""

import argparse
import hashlib
import json
from fractions import Fraction as Q
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paradox_dynamics import simulate
from paradox_dynamics.engine import SCHEDULES
from paradox_dynamics.plotting import plot_trajectory


def reproduce(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    runs = {}

    def record(name, model, initial, **kwargs):
        run = simulate(model, initial, **kwargs)
        run.save(output / name)
        runs[name] = run
        return run

    def savefig(figure, name):
        figure.savefig(output / f"{name}.png", dpi=160)
        plt.close(figure)

    liar = record("liar", "liar", "1/4", steps=12, precision="rational")
    savefig(plot_trajectory(liar), "liar")

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
    for ax, model, title in zip(
        axes, ["k-sayer", "minimalist"], ["Half-Sayer: attraction", "Minimalist: repulsion"]
    ):
        for index, initial in enumerate([Q(2, 3) - Q(1, 10000), Q(2, 3), Q(2, 3) + Q(1, 10000)]):
            run = record(f"{model}-{index}", model, initial, steps=22, precision="rational")
            label = ["2/3 − 1/10000", "exactly 2/3", "2/3 + 1/10000"][index]
            ax.plot(run.array()[:, 0], ".-", label=label, linewidth=1, markersize=3)
        ax.set(title=title, xlabel="Revision", ylabel="Semantic value")
        ax.legend(fontsize=8)
    savefig(fig, "stability")

    fig, axes = plt.subplots(3, 1, figsize=(9, 7), sharex=True, constrained_layout=True)
    for ax, precision in zip(axes, ["float32", "float64", "rational"]):
        run = record(f"tent-{precision}", "chaotic-liar", "0.314", steps=120, precision=precision)
        values = run.array()[:, 0]
        ax.plot(values, ".-", markersize=3, linewidth=0.8)
        zero = next((i for i, (v,) in enumerate(run.states) if v == 0), None)
        title = (
            f"{precision}: first zero at n={zero}"
            if zero is not None
            else (f"{precision}: recurrence {run.diagnostics()['recurrence']}")
        )
        ax.set(title=title, ylim=(-0.03, 1.03), ylabel="x")
    axes[-1].set_xlabel("Revision")
    fig.suptitle("Same requested initial value 0.314; different arithmetic")
    savefig(fig, "precision")

    a = record("tent-near-a", "chaotic-liar", "0.314", steps=20, precision="rational")
    b = record("tent-near-b", "chaotic-liar", "0.3141", steps=20, precision="rational")
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True, constrained_layout=True)
    axes[0].plot(a.array()[:, 0], ".-", label="x0 = 0.314")
    axes[0].plot(b.array()[:, 0], ".-", label="x0 = 0.3141")
    axes[0].set(ylabel="x", title="Exact rational trajectories: the paper's p. 671 example")
    axes[0].legend()
    differences = [abs(x[0] - y[0]) for x, y in zip(a.states, b.states)]
    axes[1].semilogy([float(d) for d in differences], ".-", label="Actual separation")
    axes[1].semilogy(range(10), [1e-4 * 2**i for i in range(10)], "--", label="2ⁿ × initial gap")
    axes[1].set(xlabel="Revision", ylabel="Absolute separation")
    axes[1].legend()
    savefig(fig, "sensitivity")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
    for ax, schedule in zip(axes, SCHEDULES):
        run = record(
            f"simple-dual-{schedule}",
            "dualist",
            ["1/4", "1/8"],
            steps=12,
            precision="rational",
            schedule=schedule,
        )
        ax.plot(run.array()[:, 0], ".-", label="x")
        ax.plot(run.array()[:, 1], ".-", label="y")
        ax.set(
            title=f"{schedule}\nperiod {run.diagnostics()['recurrence']['period']}",
            xlabel="Full sweep",
            ylim=(-0.03, 1.03),
        )
        ax.legend()
    savefig(fig, "simple-dual-schedules")

    # Long rational starts give a different experiment from the short decimals
    # in the paper. Retain all points and mark the first one; no hidden burn-in.
    long_start = ["0.314159265358979323846", "0.271828182845904523536"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), constrained_layout=True)
    for ax, schedule in zip(axes, SCHEDULES):
        run = record(
            f"dual-long-{schedule}",
            "dual-revision",
            long_start,
            steps=6000,
            precision="rational",
            schedule=schedule,
        )
        data = run.array()
        ax.scatter(data[1:, 0], data[1:, 1], s=1, alpha=0.4)
        ax.scatter(*data[0], color="#c24e18", marker="x", s=45, label="Initial state")
        ax.set(
            title=schedule,
            xlabel="x",
            ylabel="y",
            aspect="equal",
            xlim=(-0.03, 1.03),
            ylim=(-0.03, 1.03),
        )
        ax.legend(fontsize=8)
    fig.suptitle("6,000 exact rational sweeps; a finite orbit plot, not an attractor proof")
    savefig(fig, "dual-schedules")

    for precision in ["float32", "float64", "rational"]:
        record(
            f"dual-short-{precision}",
            "dual-revision",
            ["0.1", "0.9"],
            steps=200,
            precision=precision,
            schedule="x-then-y",
        )

    curry = record(
        "curry-cycle", "curry", "1/5", parameters={"p": "3/4"}, steps=20, precision="rational"
    )
    savefig(plot_trajectory(curry), "curry")
    record("curry-boundary", "curry", "0.23", parameters={"p": "1"}, steps=5, precision="rational")

    # A diagnostic control: positive local expansion on an exactly fixed orbit.
    record("tent-repelling-fixed-point", "chaotic-liar", "2/3", steps=20, precision="rational")
    summary = {
        "description": "Original experiments under selected Mar–Grim equations",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "experiments": {
            name: {
                "model": run.model,
                "precision": run.precision,
                "schedule": run.schedule,
                "steps": len(run.states) - 1,
                "initial": run.requested_initial,
                "parameters": run.requested_parameters,
                "diagnostics": run.diagnostics(),
                "first_zero": next(
                    (i for i, row in enumerate(run.states) if all(v == 0 for v in row)), None
                ),
            }
            for name, run in runs.items()
        },
        "software": liar.report()["software"],
        "figure_files": sorted(p.name for p in output.glob("*.png")),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(f"Saved {len(runs)} experiments and {len(summary['figure_files'])} figures to {output}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results"))
    reproduce(parser.parse_args().out)
