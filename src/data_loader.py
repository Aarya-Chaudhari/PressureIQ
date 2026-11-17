from __future__ import annotations

from pathlib import Path
import pandas as pd


def discover_csv_files(raw_dir: Path):
    raw_dir = Path(raw_dir)
    files = sorted(
        [f for f in raw_dir.iterdir() if f.is_file() and f.suffix.lower() == ".csv" and not f.name.startswith("._")],
        key=lambda p: p.name,
    )
    return files


def load_csv(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    return pd.read_csv(p)


def load_all_datasets(raw_dir: str | Path) -> dict[str, pd.DataFrame]:
    raw_dir = Path(raw_dir)
    data = {}
    for file in discover_csv_files(raw_dir):
        key = file.stem
        data[key] = load_csv(file)
    return data


def data_summary(raw_dir: str | Path):
    datasets = load_all_datasets(raw_dir)
    summary = []
    for name, df in datasets.items():
        summary.append({
            "file": f"{name}.csv",
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": ", ".join(df.columns.tolist()),
            "missing_values": int(df.isna().sum().sum()),
            "duplicates": int(df.duplicated().sum()),
        })
    return pd.DataFrame(summary)
