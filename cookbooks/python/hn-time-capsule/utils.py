"""Utilities for HN Time Capsule pipeline."""

import json
from pathlib import Path


def save_intermediate(results, step_name: str) -> None:
    """Save intermediate results to intermediate/{step_name}/."""
    step_dir = Path(f"intermediate/{step_name}")
    step_dir.mkdir(parents=True, exist_ok=True)
    for r in results:
        item_dir = step_dir / f"item_{r.meta.item_index:02d}"
        item_dir.mkdir(exist_ok=True)
        (item_dir / "status.txt").write_text(r.status)
        if r.data:
            (item_dir / "data.json").write_text(json.dumps(r.data.model_dump(), indent=2))
        if r.error:
            (item_dir / "error.txt").write_text(r.error)
