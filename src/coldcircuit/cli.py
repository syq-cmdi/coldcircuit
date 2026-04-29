from pathlib import Path
import json
import typer
from rich import print

from .io import load_plate_json, save_schema
from .report import render_markdown_report
from .optimization import optimize_grid
from .backends.openfoam import write_openfoam_case_placeholder
from .design_rules import all_rules_grouped
from .tdp1500 import make_tdp1500_reference_design, make_tdp1500_3d_stack, tdp1500_guidance

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


@app.command("rules")
def structure_rules(out: Path | None = typer.Option(None, help="Optional JSON output path")):
    grouped = all_rules_grouped()
    if out:
        out.write_text(json.dumps(grouped, indent=2), encoding="utf-8")
        print(f"[green]Structure rules written to {out}[/green]")
    else:
        print(json.dumps(grouped, indent=2))


@app.command("tdp1500")
def tdp1500_reference(out: Path = typer.Option(Path("tdp1500_reference.json")), stack_out: Path = typer.Option(Path("tdp1500_3d_stack.json"))):
    plate = make_tdp1500_reference_design()
    stack = make_tdp1500_3d_stack()
    out.write_text(plate.model_dump_json(indent=2), encoding="utf-8")
    stack_out.write_text(stack.model_dump_json(indent=2), encoding="utf-8")
    print(f"[green]1500W reference design written to {out}[/green]")
    print(f"[green]1500W 3D stack written to {stack_out}[/green]")
    print(tdp1500_guidance().model_dump_json(indent=2))


if __name__ == "__main__":
    app()
