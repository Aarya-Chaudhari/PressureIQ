from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def batting_metrics(processed: pd.DataFrame):
    df = processed.copy()
    df["batter_runs"] = df["runs"].apply(lambda x: int(x or 0))
    df["legal_batters"] = df["striker_id"].notna() & df["legal_delivery"].astype(bool)
    df["balls_faced"] = np.where(df["legal_batters"], 1, 0)
    df["is_boundary"] = (df["is_four"] == True) | (df["is_six"] == True)
    df["is_dot"] = (df["runs"] == 0) & (df["extras_type"].isna() | (df["extras_type"].astype(str).str.lower().isin(["none", "nan"])))
    df["dismissed_by_batter"] = (df["is_wicket"] == True) & (df["dismissal_type"].fillna("").str.lower().isin(["caught", "bowled", "lbw", "stumped", "run out", "hit wicket"]))

    pressure = df[df["batting_pressure_flag"].isin(["High", "Medium"])].copy()
    normal = df[df["batting_pressure_flag"] == "Normal"].copy()

    results = []
    for player_id, player_df in df.groupby("striker_id"):
        p = player_df.copy()
        if p.empty:
            continue
        total_runs = int(p["batter_runs"].sum())
        balls = int((p["balls_faced"] == 1).sum())
        strike_rate = (total_runs / max(balls, 1)) * 100.0
        boundary_pct = (p["is_boundary"].sum() / max(balls, 1)) * 100.0
        dot_pct = (p["is_dot"].sum() / max(balls, 1)) * 100.0
        dismissals = int(p["dismissed_by_batter"].sum())
        dismissal_rate = (dismissals / max(len(p), 1)) * 100.0
        results.append({
            "player_id": player_id,
            "player_name": p["striker_name"].dropna().iloc[0],
            "total_runs": total_runs,
            "balls_faced": balls,
            "strike_rate": strike_rate,
            "boundary_pct": boundary_pct,
            "dot_pct": dot_pct,
            "dismissals": dismissals,
            "dismissal_rate": dismissal_rate,
            "pressure_balls": int(pressure[pressure["striker_id"] == player_id].shape[0]),
            "pressure_matches": int(pressure[pressure["striker_id"] == player_id]["match_id"].nunique()),
            "normal_balls": int(normal[normal["striker_id"] == player_id].shape[0]),
            "normal_matches": int(normal[normal["striker_id"] == player_id]["match_id"].nunique()),
            "pressure_score": pressure[pressure["striker_id"] == player_id]["batting_pressure_score"].mean() if not pressure[pressure["striker_id"] == player_id].empty else 0,
            "normal_score": normal[normal["striker_id"] == player_id]["batting_pressure_score"].mean() if not normal[normal["striker_id"] == player_id].empty else 0,
        })

    player_stats = pd.DataFrame(results)
    if not player_stats.empty:
        pressure_df = player_stats[player_stats["pressure_balls"] > 0].copy()
        pressure_df["sr_z"] = zscore(pressure_df["strike_rate"])
        pressure_df["bx_z"] = zscore(pressure_df["boundary_pct"])
        pressure_df["dot_z"] = zscore(pressure_df["dot_pct"])
        pressure_df["dismiss_z"] = zscore(pressure_df["dismissal_rate"])
        pressure_df["pressure_bpq"] = 0.35 * pressure_df["sr_z"] - 0.20 * pressure_df["bx_z"] - 0.20 * pressure_df["dot_z"] + 0.25 * pressure_df["dismiss_z"]

        normal_df = player_stats[player_stats["normal_balls"] > 0].copy()
        normal_df["sr_z"] = zscore(normal_df["strike_rate"])
        normal_df["bx_z"] = zscore(normal_df["boundary_pct"])
        normal_df["dot_z"] = zscore(normal_df["dot_pct"])
        normal_df["dismiss_z"] = zscore(normal_df["dismissal_rate"])
        normal_df["normal_bpq"] = 0.35 * normal_df["sr_z"] - 0.20 * normal_df["bx_z"] - 0.20 * normal_df["dot_z"] + 0.25 * normal_df["dismiss_z"]

        pressure_map = pressure_df.set_index("player_id")["pressure_bpq"]
        normal_map = normal_df.set_index("player_id")["normal_bpq"]
        player_stats = player_stats.merge(pressure_map.rename("pressure_bpq"), on="player_id", how="left")
        player_stats = player_stats.merge(normal_map.rename("normal_bpq"), on="player_id", how="left")
        player_stats["pressure_bpq"] = player_stats["pressure_bpq"].fillna(0)
        player_stats["normal_bpq"] = player_stats["normal_bpq"].fillna(0)
        player_stats["batting_uplift"] = player_stats["pressure_bpq"] - player_stats["normal_bpq"]
        player_stats["raw_batting_score"] = 0.70 * player_stats["pressure_bpq"] - 0.30 * player_stats["batting_uplift"]
        player_stats["sample_share"] = player_stats["pressure_balls"] / (player_stats["pressure_balls"] + 25)
        player_stats["final_adjusted_score"] = player_stats["sample_share"] * player_stats["raw_batting_score"] + (1 - player_stats["sample_share"]) * player_stats["normal_bpq"]
    else:
        player_stats = pd.DataFrame(columns=["player_id","player_name","pressure_balls","pressure_matches","normal_balls","normal_matches","pressure_bpq","normal_bpq","batting_uplift","raw_batting_score","final_adjusted_score"])

    return player_stats


def zscore(series: pd.Series):
    series = pd.to_numeric(series, errors="coerce")
    if series.empty or series.nunique() <= 1:
        return pd.Series(0.0, index=series.index)
    z = (series - series.mean()) / series.std(ddof=0)
    return z.fillna(0.0)
