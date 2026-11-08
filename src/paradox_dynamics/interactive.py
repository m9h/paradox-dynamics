"""Optional notebook controls backed by the same tested Python simulator."""

from .engine import PRECISIONS, SCHEDULES, simulate
from .models import MODELS


def explorer():
    import ipywidgets as widgets
    import matplotlib.pyplot as plt
    from IPython.display import display

    from .plotting import plot_trajectory

    model = widgets.Dropdown(options=list(MODELS), description="Map:")
    x = widgets.Text(value="0.314", description="Initial x:")
    y = widgets.Text(value="0.9", description="Initial y:", disabled=True)
    parameter = widgets.Text(value="", description="Parameter:", disabled=True)
    precision = widgets.Dropdown(
        options=list(PRECISIONS), value="rational", description="Arithmetic:"
    )
    schedule = widgets.Dropdown(options=SCHEDULES, description="Schedule:", disabled=True)
    steps = widgets.IntSlider(
        value=40, min=1, max=300, description="Steps:", continuous_update=False
    )
    button = widgets.Button(description="Run experiment", button_style="primary")
    output = widgets.Output()

    def configure(change):
        spec = MODELS[model.value]
        y.disabled = spec.dimension == 1
        schedule.disabled = spec.dimension == 1
        if spec.dimension == 1:
            schedule.value = "simultaneous"
        parameter.disabled = spec.parameter is None
        parameter.description = f"{spec.parameter}:" if spec.parameter else "Parameter:"
        parameter.value = spec.default or ""

    def draw(_):
        with output:
            output.clear_output(wait=True)
            spec = MODELS[model.value]
            initial = [x.value, y.value][: spec.dimension]
            params = {spec.parameter: parameter.value} if spec.parameter else {}
            try:
                run = simulate(
                    model.value,
                    initial,
                    steps=steps.value,
                    precision=precision.value,
                    schedule=schedule.value,
                    parameters=params,
                )
            except (ValueError, ZeroDivisionError, OverflowError) as exc:
                print(f"Check the inputs: {exc}")
                return
            print(spec.equation)
            print(f"Mar & Grim, printed pp. {spec.pages}; one step = one complete sweep.")
            print("First stored-state recurrence:", run.diagnostics()["recurrence"])
            print("A recurrence or positive local expansion rate is not a chaos classification.")
            figure = plot_trajectory(run)
            display(figure)
            plt.close(figure)

    model.observe(configure, names="value")
    button.on_click(draw)
    return widgets.VBox(
        [
            widgets.HTML("<b>Revision-map explorer</b> — decimal/fraction inputs are accepted."),
            widgets.HBox([model, precision]),
            widgets.HBox([x, y]),
            widgets.HBox([parameter, schedule]),
            steps,
            button,
            output,
        ]
    )
