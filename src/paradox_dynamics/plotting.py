"""Original plots. Rendering converts exact values to float64, never the dynamics."""

import matplotlib.pyplot as plt
import numpy as np

from .models import MODELS, scalar_value


def plot_trajectory(run, *, cobweb_steps=20):
    values = run.array()
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
    for i, label in enumerate(("x", "y")[: values.shape[1]]):
        axes[0].plot(values[:, i], ".-", markersize=3, linewidth=1, label=label)
    axes[0].set(xlabel="Revision / full sweep", ylabel="Semantic value", ylim=(-0.03, 1.03))
    axes[0].legend()
    if values.shape[1] == 1:
        grid = np.linspace(0, 1, 501)
        params = {k: np.float64(v) for k, v in run.parameters.items()}
        axes[1].plot(grid, [scalar_value(run.model, x, params) for x in grid], label="f(x)")
        axes[1].plot(grid, grid, color="0.6", linestyle="--", label="y = x")
        points = [(values[0, 0], 0)]
        for old, new in zip(values[:cobweb_steps, 0], values[1 : cobweb_steps + 1, 0]):
            points.extend([(old, new), (new, new)])
        axes[1].plot(*np.array(points).T, color="#c24e18", alpha=0.75, linewidth=1)
        axes[1].set(
            xlabel="x", ylabel="f(x)", title=f"First {min(cobweb_steps, len(values) - 1)} steps"
        )
        axes[1].legend()
    else:
        scatter = axes[1].scatter(
            values[:, 0], values[:, 1], c=np.arange(len(values)), s=8, cmap="viridis"
        )
        fig.colorbar(scatter, ax=axes[1], label="Full sweep")
        axes[1].set(xlabel="x", ylabel="y", title="State-space orbit")
    axes[1].set(xlim=(-0.03, 1.03), ylim=(-0.03, 1.03), aspect="equal")
    fig.suptitle(f"{MODELS[run.model].title} · {run.precision} · {run.schedule}", fontsize=11)
    return fig
