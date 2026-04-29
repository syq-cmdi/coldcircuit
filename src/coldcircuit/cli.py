from pathlib import Path
import json
import typer
from rich import print

from .io import load_plate_json, save_schema
from .report import render_markdown_report
from .optimization import optimize_grid
from .backends.openfoam import write_openfoam_case_placeholder

app = typer.Typer(help="ColdCircuit liquid cold plate design CLI")


@app.command()
def validate(json_path: Path = typer.Argument(..., help="Cold plate JSON specification")):
    plate = load_plate_json(json_path)
    print(f"[green]Valid ColdCircuit design:[/green] {plate.name}")
    for c in plate.manufacturability_checks():
        print(f"{c.severity.upper()} [{c.item}] {c.message}")


@app.command()
def simulate(json_path: Path, coolant_inlet_c: float = typer.Option(25.0, help="Coolant inlet temperature, °C")):
    plate = load_plate_json(json_path)
    print(plate.simulate_1d(coolant_inlet_c=coolant_inlet_c).model_dump_json(indent=2))


@app.command()
def report(json_path: Path, out: Path = typer.Option(Path("coldcircuit_report.md")), coolant_inlet_c: float = typer.Option(25.0)):
    plate = load_plate_json(json_path)
    out.write_text(render_markdown_report(plate, coolant_inlet_c=coolant_inlet_c), encoding="utf-8")
    print(f"[green]Report written to {out}[/green]")


@app.command()
def schema(out: Path = typer.Option(Path("coldcircuit_schema.json"))):
    save_schema(out)
    print(f"[green]Schema written to {out}[/green]")


@app.command()
def optimize(json_path: Path, out: Path = typer.Option(Path("optimization.json")), coolant_inlet_c: float = typer.Option(25.0)):
    plate = load_plate_json(json_path)
    variable_grid = {
        "channel.width_mm": [1.2, 1.5, 2.0, 2.5, 3.0],
        "channel.depth_mm": [1.0, 1.2, 1.5, 2.0],
        "inlet_outlet.flow_rate_lpm": [0.8, 1.0, 1.2, 1.5, 2.0, 2.5],
    }
    if hasattr(plate.primary_channel(), "pitch_mm"):
        variable_grid["channel.pitch_mm"] = [4.0, 5.0, 6.0, 8.0]
    result = optimize_grid(plate, variable_grid, coolant_inlet_c=coolant_inlet_c)
    out.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]Optimization result written to {out}[/green]")
    if result.best:
        print("[bold]Best candidate:[/bold]")
        print(json.dumps(result.best.model_dump(), indent=2))


@app.command()
def openfoam(json_path: Path, case_dir: Path = typer.Option(Path("openfoam_case"))):
    plate = load_plate_json(json_path)
    path = write_openfoam_case_placeholder(plate, case_dir)
    print(f"[green]OpenFOAM scaffold written to {path}[/green]")


if __name__ == "__main__":
    app()
