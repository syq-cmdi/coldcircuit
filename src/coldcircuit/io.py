import json
from pathlib import Path
from .plate import ColdPlate


def load_plate_json(path: str | Path) -> ColdPlate:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ColdPlate.model_validate(data)


def save_plate_json(plate: ColdPlate, path: str | Path) -> None:
    Path(path).write_text(plate.model_dump_json(indent=2), encoding="utf-8")


def save_schema(path: str | Path) -> None:
    Path(path).write_text(json.dumps(ColdPlate.model_json_schema(), indent=2), encoding="utf-8")
