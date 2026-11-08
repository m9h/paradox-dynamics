import argparse
import json
from pathlib import Path

from .engine import PRECISIONS, SCHEDULES, simulate
from .models import MODELS


def main(argv=None):
    parser = argparse.ArgumentParser(description="Explore logical paradoxes as iterated maps")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List equations and paper page references")
    command = commands.add_parser(
        "simulate", help="Export a trajectory, provenance and optional plot"
    )
    command.add_argument("model", choices=MODELS)
    command.add_argument("--initial", nargs="+", required=True, help="Decimal or fraction strings")
    command.add_argument("--steps", type=int, default=100)
    command.add_argument("--precision", choices=PRECISIONS, default="float64")
    command.add_argument("--schedule", choices=SCHEDULES, default="simultaneous")
    command.add_argument("--parameter", help="Value of k (k-sayer) or p (curry)")
    command.add_argument("--out", type=Path, required=True)
    command.add_argument("--plot", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "list":
        for key, spec in MODELS.items():
            print(f"{key:16} {spec.equation}  [pp. {spec.pages}]")
        return
    parameter = MODELS[args.model].parameter
    if args.parameter is not None and parameter is None:
        parser.error(f"{args.model} has no parameter")
    try:
        run = simulate(
            args.model,
            args.initial,
            steps=args.steps,
            precision=args.precision,
            schedule=args.schedule,
            parameters={parameter: args.parameter} if args.parameter is not None else {},
        )
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        parser.error(str(exc))
    run.save(args.out)
    if args.plot:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from .plotting import plot_trajectory

        fig = plot_trajectory(run)
        fig.savefig(args.out / "trajectory.png", dpi=160)
        plt.close(fig)
    print(json.dumps(run.diagnostics(), indent=2, allow_nan=False))
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
