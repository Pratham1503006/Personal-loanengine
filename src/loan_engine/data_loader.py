"""Load and index the CSV research datasets.

The datasets live in ``data/`` and are intentionally plain CSV so every rule
and source can be inspected without a database. This module is the single
place that knows how to turn those files into typed objects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .schemas import ApplicantProfile, Lender, Rule, Source

#: Repository root = two parents up from this file (src/loan_engine/data_loader.py).
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required dataset not found: {path}")
    # Read everything as string first, then let pydantic coerce, so that blank
    # cells stay blank (None) rather than becoming NaN/0.
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])


def _clean(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if v is None:
            out[k] = None
            continue
        s = str(v).strip()
        if s == "" or s.lower() in ("nan", "na", "n/a", "none"):
            out[k] = None
            continue
        out[k] = s
    return out


def _dir(data_dir) -> Path:
    """Normalise a data directory given as str, Path, or None."""
    return Path(data_dir) if data_dir else DATA_DIR


def load_lenders(data_dir=None) -> List[Lender]:
    df = _read_csv(_dir(data_dir) / "lenders.csv")
    return [Lender(**_clean(row)) for row in df.to_dict(orient="records")]


def load_rules(data_dir=None) -> List[Rule]:
    df = _read_csv(_dir(data_dir) / "lender_rules.csv")
    return [Rule(**_clean(row)) for row in df.to_dict(orient="records")]


def load_sources(data_dir=None) -> List[Source]:
    df = _read_csv(_dir(data_dir) / "source_registry.csv")
    return [Source(**_clean(row)) for row in df.to_dict(orient="records")]


def load_input_variables(data_dir=None) -> pd.DataFrame:
    return _read_csv(_dir(data_dir) / "input_variables.csv")


def load_test_profiles(path=None) -> List[ApplicantProfile]:
    path = Path(path) if path else (DATA_DIR / "test_profiles.json")
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    profiles: List[ApplicantProfile] = []
    for item in raw:
        if isinstance(item, dict) and "profile" in item and isinstance(item["profile"], dict):
            payload = dict(item["profile"])
            payload.setdefault("applicant_id", item.get("profile_id"))
            payload.setdefault("synthetic", True)
            profiles.append(ApplicantProfile(**payload))
        else:
            profiles.append(ApplicantProfile(**item))
    return profiles


def load_all(data_dir: Optional[Path] = None) -> Dict[str, object]:
    """Convenience loader returning every dataset keyed by name."""
    return {
        "lenders": load_lenders(data_dir),
        "rules": load_rules(data_dir),
        "sources": load_sources(data_dir),
        "input_variables": load_input_variables(data_dir),
    }


def index_by_id(items, attr: str) -> Dict[str, object]:
    return {getattr(item, attr): item for item in items}


def rules_by_lender(rules: List[Rule]) -> Dict[str, List[Rule]]:
    grouped: Dict[str, List[Rule]] = {}
    for rule in rules:
        grouped.setdefault(rule.lender_id, []).append(rule)
    return grouped


def sources_by_id(sources: List[Source]) -> Dict[str, Source]:
    return {s.source_id: s for s in sources}
