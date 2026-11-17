from __future__ import annotations

import pandas as pd
import numpy as np


def bowling_metrics(processed: pd.DataFrame):
    df = processed.copy()
    df["legal_ball_bowled"] = df["legal_delivery"].fillna(False)
    df["bowler_runs_conceded"] = df["runs"].apply(lambda x: int(x or 0))
    df["bowler_wicket"] = df["is_wicket"].fillna(False) & df["dismissal_type"].fillna("").str.lower().isin(["caught", "bowled", "lbw", "stumped", "caught and bowled"]) 

    pressure = df[df["bowling_pressure_flag"].isin(["High", "Medium"])].copy()
    normal = df[df["bowling_pressure_flag"] == "Normal"].copy()

    results = []
    for player_id, player_df in df.groupby("bowler_id"):
        if player_df.empty:
            continue
        legal_balls = int((player_df["legal_ball_bowled"] == True).sum())
        runs = int(player_df["bowler_runs_conceded"].sum())
        wickets = int(player_df["bowler_wicket"].sum())
        economy = (runs / max(legal_balls / 6, 1)) if legal_balls else 0
        wicket_rate = (wickets / max(legal_balls / 6, 1)) if legal_balls else 0
        dot_pct = (player_df["runs"].eq(0).sum() / max(legal_balls, 1)) * 100.0
        boundary_pct = (player_df["is_four"].fillna(False).sum() + player_df["is_six"].fillna(False).sum()) / max(legal_balls, 1) * 100.0
        results.append({
            "player_id": player_id,
            "player_name": player_df["bowler_name"].dropna().iloc[0],
            "legal_balls": legal_balls,
            "runs_conceded": runs,
            "wickets": wickets,
            "economy": economy,
            "wicket_rate": wicket_rate,
            "dot_pct": dot_pct,
            "boundary_pct": boundary_pct,
            "pressure_balls": int(pressure[pressure["bowler_id"] == player_id].shape[0]),
            "pressure_matches": int(pressure[pressure["bowler_id"] == player_id]["match_id"].nunique()),
            "normal_balls": int(normal[normal["bowler_id"] == player_id].shape[0]),
            "normal_matches": int(normal[normal["bowler_id"] == player_id]["match_id"].nunique()),
        })

    bowler_stats = pd.DataFrame(results)
    if not bowler_stats.empty:
        pressure_df = bowler_stats[bowler_stats["pressure_balls"] > 0].copy()
        pressure_df["wicket_z"] = zscore(pressure_df["wicket_rate"])
        pressure_df["dot_z"] = zscore(pressure_df["dot_pct"])
        pressure_df["eco_z"] = zscore(pressure_df["economy"])  # higher economy is worse, handled with negative weight later
        pressure_df["boundary_z"] = zscore(pressure_df["boundary_pct"])
        pressure_df["pressure_bq"] = 0.30 * pressure_df["wicket_z"] + 0.30 * pressure_df["dot_z"] - 0.25 * pressure_df["eco_z"] - 0.15 * pressure_df["boundary_z"]

        normal_df = bowler_stats[bowler_stats["normal_balls"] > 0].copy()
        normal_df["wicket_z"] = zscore(normal_df["wicket_rate"])
        normal_df["dot_z"] = zscore(normal_df["dot_pct"])
        normal_df["eco_z"] = zscore(normal_df["economy"])
        normal_df["boundary_z"] = zscore(normal_df["boundary_pct"])
        normal_df["normal_bq"] = 0.30 * normal_df["wicket_z"] + 0.30 * normal_df["dot_z"] - 0.25 * normal_df["eco_z"] - 0.15 * normal_df["boundary_z"]

        pressure_map = pressure_df.set_index("player_id")["pressure_bq"]
        normal_map = normal_df.set_index("player_id")["normal_bq"]
        bowler_stats = bowler_stats.merge(pressure_map.rename("pressure_bq"), on="player_id", how="left")
        bowler_stats = bowler_stats.merge(normal_map.rename("normal_bq"), on="player_id", how="left")
        bowler_stats["pressure_bq"] = bowler_stats["pressure_bq"].fillna(0)
        bowler_stats["normal_bq"] = bowler_stats["normal_bq"].fillna(0)
        bowler_stats["bowling_uplift"] = bowler_stats["pressure_bq"] - bowler_stats["normal_bq"]
        bowler_stats["raw_bowling_score"] = 0.70 * bowler_stats["pressure_bq"] - 0.30 * bowler_stats["bowling_uplift"]
        bowler_stats["sample_share"] = bowler_stats["pressure_balls"] / (bowler_stats["pressure_balls"] + 25)
        bowler_stats["final_adjusted_score"] = bowler_stats["sample_share"] * bowler_stats["raw_bowling_score"] + (1 - bowler_stats["sample_share"]) * bowler_stats["normal_bq"]
    else:
        bowler_stats = pd.DataFrame(columns=["player_id","player_name","pressure_balls","pressure_matches","normal_balls","normal_matches","pressure_bq","normal_bq","bowling_uplift","raw_bowling_score","final_adjusted_score"])

    return bowler_stats


def zscore(series: pd.Series):
    series = pd.to_numeric(series, errors="coerce")
    if series.empty or series.nunique() <= 1:
        return pd.Series(0.0, index=series.index)
    z = (series - series.mean()) / series.std(ddof=0)
    return z.fillna(0.0)
