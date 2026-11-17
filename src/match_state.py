from __future__ import annotations

from pathlib import Path
import pandas as pd


def innings_total_balls(row: pd.Series) -> int:
    if pd.notna(row.get("first_inn_revised_overs")) and row.get("first_inn_revised_overs") is not None:
        return max(6, int(float(row["first_inn_revised_overs"]) * 6))
    if pd.notna(row.get("second_inn_revised_overs")) and row.get("second_inn_revised_overs") is not None:
        return max(6, int(float(row["second_inn_revised_overs"]) * 6))
    return 120


def classify_innings_phase(balls_remaining: float, total_balls: int, innings_number: int, chasing: bool):
    if total_balls <= 0:
        return "Normal"
    fraction = balls_remaining / max(total_balls, 1)
    if innings_number == 1:
        if balls_remaining >= total_balls * 0.55:
            return "Powerplay"
        if balls_remaining >= total_balls * 0.25:
            return "Middle overs"
        return "Death overs"
    if chasing:
        if fraction >= 0.55:
            return "Chase build-up"
        if fraction >= 0.25:
            return "Middle overs"
        return "Death overs"
    if fraction >= 0.55:
        return "Set-up"
    if fraction >= 0.25:
        return "Middle overs"
    return "Death overs"


def reconstruct_match_state(clean_df: pd.DataFrame, matches_df: pd.DataFrame, competitions_df: pd.DataFrame, output_csv: str | Path):
    cleaned = clean_df.copy()
    cleaned["match_date"] = pd.to_datetime(cleaned["match_date"], errors="coerce")
    cleaned = cleaned.sort_values(["match_id", "innings", "overid", "over_ball_num"]).reset_index(drop=True)

    match_lookup = matches_df.set_index("match_id")
    comp_lookup = competitions_df.set_index("comp_id")
    first_innings_totals = cleaned[cleaned["innings"] == 1].groupby("match_id")["runs"].sum().to_dict()

    rows = []
    for (match_id, innings), group in cleaned.groupby(["match_id", "innings"], sort=True):
        match_meta = match_lookup.loc[match_id] if match_id in match_lookup.index else pd.Series(dtype=object)
        comp_id = match_meta.get("comp_id") if isinstance(match_meta, pd.Series) else None
        comp_name = comp_lookup.loc[comp_id, "comp_name"] if comp_id in comp_lookup.index else None
        season = comp_lookup.loc[comp_id, "season"] if comp_id in comp_lookup.index else None

        total_balls = innings_total_balls(match_meta) if hasattr(match_meta, "get") else 120
        target_score = None
        chasing = False
        if innings == 2:
            revised_target = match_meta.get("revised_target") if hasattr(match_meta, "get") else None
            if pd.notna(revised_target):
                target_score = float(revised_target)
            else:
                target_score = float(first_innings_totals.get(match_id, 0) + 1)
            chasing = True

        score_before = 0
        wickets_before = 0
        legal_balls_before = 0
        for _, row in group.iterrows():
            pre_delivery_legal_balls = legal_balls_before
            current_rr = (score_before / max(pre_delivery_legal_balls / 6, 1e-6)) if pre_delivery_legal_balls > 0 else 0.0
            extras_val = row.get("extras_type")
            legal_delivery = pd.isna(extras_val) or (str(extras_val).strip().lower() not in {"wide", "no_ball", "no ball"})
            balls_remaining = max(total_balls - pre_delivery_legal_balls, 0)
            runs_required = None if target_score is None else max(target_score - score_before, 0)
            required_rr = None if runs_required is None or balls_remaining <= 0 else (runs_required * 6) / max(balls_remaining, 1)
            innings_phase = classify_innings_phase(balls_remaining, total_balls, innings, chasing)

            rows.append({
                "match_id": match_id,
                "innings": innings,
                "competition": comp_name,
                "season": season,
                "match_date": row.get("match_date"),
                "batting_team_id": row.get("batting_team_id"),
                "bowling_team_id": row.get("bowling_team_id"),
                "striker_id": row.get("striker_id"),
                "striker_name": row.get("striker_name"),
                "bowler_id": row.get("bowler_id"),
                "bowler_name": row.get("bowler_name"),
                "score_before_delivery": score_before,
                "wickets_before_delivery": wickets_before,
                "wickets_remaining": max(10 - wickets_before, 0),
                "legal_balls_before_delivery": pre_delivery_legal_balls,
                "total_innings_balls": total_balls,
                "balls_remaining": balls_remaining,
                "current_run_rate": round(current_rr, 3),
                "target_score": target_score,
                "runs_required": runs_required,
                "required_run_rate": round(required_rr, 3) if required_rr is not None else None,
                "innings_phase": innings_phase,
                "legal_delivery": bool(legal_delivery),
                "runs": row.get("runs"),
                "extras_type": row.get("extras_type"),
                "is_wicket": bool(row.get("is_wicket")),
                "dismissal_type": row.get("dismissal_type"),
                "is_four": bool(row.get("is_four")),
                "is_six": bool(row.get("is_six")),
                "dismissed_player_id": row.get("dismissed_player_id"),
            })

            if legal_delivery:
                legal_balls_before += 1
            if row.get("is_wicket"):
                wickets_before += 1
            score_before += int(row.get("runs", 0) or 0)

    output_df = pd.DataFrame(rows)
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    return output_df
