from __future__ import annotations

from pathlib import Path
import pandas as pd

from src.data_loader import load_all_datasets


def audit_datasets(raw_dir: str | Path, output_csv: str | Path):
    datasets = load_all_datasets(raw_dir)
    rows = []
    for name, df in datasets.items():
        rows.append({
            "file_name": f"{name}.csv",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": "; ".join(df.columns.tolist()),
            "dtypes": str(df.dtypes.to_dict()),
            "missing_values": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "primary_key_candidates": infer_primary_keys(df),
            "foreign_key_candidates": infer_foreign_keys(df),
        })
    audit_df = pd.DataFrame(rows)
    audit_df.to_csv(output_csv, index=False)
    return audit_df


def infer_primary_keys(df: pd.DataFrame):
    candidates = []
    for col in df.columns:
        if df[col].notna().all() and df[col].is_unique:
            candidates.append(col)
    return "; ".join(candidates)


def infer_foreign_keys(df: pd.DataFrame):
    candidates = []
    for col in df.columns:
        if "id" in col.lower() or "team" in col.lower() or "player" in col.lower() or "comp" in col.lower():
            if df[col].notna().sum() > 0:
                candidates.append(col)
    return "; ".join(candidates)


def build_data_dictionary(raw_dir: str | Path, output_csv: str | Path):
    datasets = load_all_datasets(raw_dir)
    records = []
    for name, df in datasets.items():
        for column in df.columns:
            records.append({
                "file_name": f"{name}.csv",
                "column_name": column,
                "dtype": str(df[column].dtype),
                "missing_values": int(df[column].isna().sum()),
                "unique_count": int(df[column].nunique(dropna=True)),
                "sample_values": str(df[column].dropna().head(5).tolist()),
            })
    dictionary_df = pd.DataFrame(records)
    dictionary_df.to_csv(output_csv, index=False)
    return dictionary_df


def generate_data_quality_report(raw_dir: str | Path, audit_df: pd.DataFrame, output_md: str | Path):
    summary = audit_df.copy()
    file_count = len(summary)
    total_rows = int(summary["rows"].sum())
    total_missing = int(summary["missing_values"].sum())
    markdown = [
        "# Data Quality Report",
        "",
        f"- Files audited: {file_count}",
        f"- Total rows: {total_rows}",
        f"- Total missing values: {total_missing}",
        "",
        "## Audit Highlights",
        "",
    ]
    for _, row in summary.iterrows():
        markdown.append(f"- **{row['file_name']}**: {row['rows']} rows, {row['columns']} columns, {row['duplicate_rows']} duplicate rows.")
    markdown.append("")
    markdown.append("## Data quality notes")
    markdown.append("- Raw CSV files were inspected without modification.")
    markdown.append("- Player identities are recovered from competition_team_player_mapping and playing_eleven tables, not from a standalone player registry.")
    markdown.append("- Match state is reconstructed from ball-by-ball sequence order and competition metadata.")
    Path(output_md).write_text("\n".join(markdown), encoding="utf-8")


def clean_core_tables(raw_dir: str | Path):
    datasets = load_all_datasets(raw_dir)
    ball = datasets["ball_by_ball"].copy()
    matches = datasets["matches"].copy()
    competitions = datasets["competitions"].copy()
    teams = datasets["teams"].copy()
    player_map = datasets["competition_team_player_mapping"].copy()
    playing_eleven = datasets["playing_eleven"].copy()

    ball = ball.drop_duplicates()
    matches = matches.drop_duplicates()
    competitions = competitions.drop_duplicates()
    teams = teams.drop_duplicates()
    player_map = player_map.drop_duplicates()
    playing_eleven = playing_eleven.drop_duplicates()

    filtered = ball.merge(matches[["match_id", "comp_id", "match_date", "home_team_id", "away_team_id", "win_team_id", "result", "first_inn_revised_overs", "second_inn_revised_overs", "revised_target"]], on="match_id", how="left")
    filtered = filtered.merge(competitions[["comp_id", "comp_name", "match_format", "season"]], on="comp_id", how="left")
    filtered = filtered.merge(teams[["comp_id", "team_id", "team_name"]].rename(columns={"team_name": "team_name_ref"}), how="left", left_on=["batting_team_id", "comp_id"], right_on=["team_id", "comp_id"]) 
    filtered = filtered.rename(columns={"team_name_ref": "batting_team_name"})
    filtered = filtered.merge(teams[["comp_id", "team_id", "team_name"]].rename(columns={"team_name": "team_name_ref"}), how="left", left_on=["bowling_team_id", "comp_id"], right_on=["team_id", "comp_id"]) 
    filtered = filtered.rename(columns={"team_name_ref": "bowling_team_name"})

    filtered = filtered.sort_values(["match_id", "innings", "overid", "over_ball_num"]).reset_index(drop=True)
    return filtered, matches, competitions, teams, player_map, playing_eleven
