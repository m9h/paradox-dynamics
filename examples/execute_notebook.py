"""Execute the tutorial with this environment's Python, independent of Jupyter config."""

import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import nbformat
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpec
from nbclient import NotebookClient


def execute(output):
    root = Path(__file__).resolve().parents[1]
    notebook = nbformat.read(root / "examples/paradox_lab.ipynb", as_version=4)
    # Keep the kernel tied to the locked environment, not a user's global python3.
    with TemporaryDirectory(prefix="paradox-kernel-") as runtime:
        manager = KernelManager()
        manager._kernel_spec = KernelSpec(
            argv=[sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            display_name="Paradox dynamics",
            language="python",
            env={"MPLBACKEND": "module://matplotlib_inline.backend_inline"},
        )
        manager.connection_file = str(Path(runtime) / "connection.json")
        client = NotebookClient(
            notebook,
            km=manager,
            timeout=120,
            resources={"metadata": {"path": str(root)}},
            store_widget_state=False,
        )
        try:
            client.execute()
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
            manager.cleanup_resources()
    # Interactive controls can be recreated locally. Keep saved output portable.
    notebook.metadata.pop("widgets", None)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output)
    count = sum(cell.cell_type == "code" for cell in notebook.cells)
    print(f"Executed {count} code cells: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("scratch/paradox_lab.ipynb"))
    execute(parser.parse_args().output)
