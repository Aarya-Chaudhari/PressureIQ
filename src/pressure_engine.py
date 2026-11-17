from __future__ import annotations

import numpy as np
import pandas as pd


def normalize_to_0_100(values: pd.Series, lower: float | None = None, upper: float | None = None):
    vals = pd.to_numeric(values, errors="coerce")
    if lower is None:
        lower = vals.min()
    if upper is None:
        upper = vals.max()
    span = upper - lower
    if span == 0:
        return pd.Series(50.0, index=vals.index)
    return ((vals - lower) / span) * 100.0


def compute_pressure_scores(processed: pd.DataFrame, config: dict):
    df = processed.copy()
    batting_threshold = config["pressure"]["batting_high_threshold"]
    bowling_threshold = config["pressure"]["bowling_high_threshold"]

    df["required_run_rate"] = pd.to_numeric(df["required_run_rate"], errors="coerce").fillna(0)
    df["current_run_rate"] = pd.to_numeric(df["current_run_rate"], errors="coerce").fillna(0)
    df["wickets_before_delivery"] = pd.to_numeric(df["wickets_before_delivery"], errors="coerce").fillna(0)
    df["wickets_remaining"] = pd.to_numeric(df["wickets_remaining"], errors="coerce").fillna(0)
    df["balls_remaining"] = pd.to_numeric(df["balls_remaining"], errors="coerce").fillna(0)
    df["total_innings_balls"] = pd.to_numeric(df["total_innings_balls"], errors="coerce").fillna(120)
    df["innings_phase"] = df["innings_phase"].fillna("Normal")

    batting_score = []
    bowling_score = []

    for _, row in df.iterrows():
        rr = row["required_run_rate"] if pd.notna(row["required_run_rate"]) else 0.0
        crr = row["current_run_rate"]
        wickets_lost = row["wickets_before_delivery"]
        wickets_left = row["wickets_remaining"]
        balls_left = row["balls_remaining"]
        total_balls = row["total_innings_balls"]
        phase = row["innings_phase"]

        score_rate_pressure = min(max((rr / max(crr + rr, 1e-6)) * 100.0, 0), 100)
        wicket_pressure = min(max((10 - wickets_lost) / 10.0 * 100.0, 0), 100)
        time_pressure = min(max((1 - (balls_left / max(total_balls, 1))) * 100.0, 0), 100)
        phase_pressure = {"Powerplay": 25, "Chase build-up": 48, "Middle overs": 52, "Death overs": 100, "Set-up": 35, "Normal": 30}.get(phase, 30)

        batting_value = (
            config["pressure"]["batting_weights"]["scoring_rate"] * score_rate_pressure
            + config["pressure"]["batting_weights"]["wicket"] * wicket_pressure
            + config["pressure"]["batting_weights"]["time"] * time_pressure
            + config["pressure"]["batting_weights"]["phase"] * phase_pressure
        )
        batting_score.append(float(np.clip(batting_value, 0, 100)))

        opp_rr = max(rr, crr)
        opp_pressure = min(max((opp_rr / max(10.0, opp_rr + 1)) * 100.0, 0), 100)
        wicket_resource = min(max((wickets_left / 10.0) * 100.0, 0), 100)
        time_context = min(max((1 - (balls_left / max(total_balls, 1))) * 100.0, 0), 100)
        closeness = min(max((10 - wickets_lost) / 10.0 * 100.0 + (1 - (balls_left / max(total_balls, 1))) * 50.0, 0), 100)

        bowling_value = (
            config["pressure"]["bowling_weights"]["opposition_rate"] * opp_pressure
            + config["pressure"]["bowling_weights"]["wicket_resource"] * wicket_resource
            + config["pressure"]["bowling_weights"]["time"] * time_context
            + config["pressure"]["bowling_weights"]["match_closeness"] * closeness
        )
        bowling_score.append(float(np.clip(bowling_value, 0, 100)))

    df["batting_pressure_score"] = batting_score
    df["bowling_pressure_score"] = bowling_score
    df["batting_pressure_flag"] = df["batting_pressure_score"].apply(lambda s: "High" if s >= batting_threshold else ("Medium" if s >= 45 else "Normal"))
    df["bowling_pressure_flag"] = df["bowling_pressure_score"].apply(lambda s: "High" if s >= bowling_threshold else ("Medium" if s >= 45 else "Normal"))
    return df
