from pathlib import Path


def build_plate_placeholder(plate):
    """Future build123d backend entrypoint."""
    try:
        import build123d as bd  # noqa: F401
    except Exception as exc:
        raise RuntimeError("build123d is not installed. Install with `pip install coldcircuit[cad]`.") from exc
    raise NotImplementedError("CAD boolean generation is not implemented in v0.2. Planned: base solid -> channel cuts -> manifold pockets -> ports -> STEP export.")


def export_step_placeholder(plate, path: str | Path) -> None:
    Path(path).write_text("ColdCircuit CAD placeholder. The v0.2 package defines the backend interface; production STEP export is planned for v0.3.\n", encoding="utf-8")
