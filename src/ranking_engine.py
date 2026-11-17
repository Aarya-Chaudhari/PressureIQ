from __future__ import annotations

import pandas as pd


def apply_eligibility_and_rank(batting_stats: pd.DataFrame, bowling_stats: pd.DataFrame, config: dict):
    batting = batting_stats.copy()
    bowling = bowling_stats.copy()

    batting["eligible"] = (batting["pressure_balls"] >= config["pressure"]["min_pressure_balls_batter"]) & (batting["pressure_matches"] >= config["pressure"]["min_pressure_matches_batter"])
    bowling["eligible"] = (bowling["pressure_balls"] >= config["pressure"]["min_pressure_balls_bowler"]) & (bowling["pressure_matches"] >= config["pressure"]["min_pressure_matches_bowler"])

    batting_rankings = batting[batting["eligible"]].sort_values("final_adjusted_score", ascending=False).reset_index(drop=True)
    bowling_rankings = bowling[bowling["eligible"]].sort_values("final_adjusted_score", ascending=False).reset_index(drop=True)

    batting_rankings.insert(0, "rank", range(1, len(batting_rankings) + 1))
    bowling_rankings.insert(0, "rank", range(1, len(bowling_rankings) + 1))

    ineligible_batting = batting[~batting["eligible"]].copy()
    ineligible_bowling = bowling[~bowling["eligible"]].copy()
    ineligible_batting["reason"] = ineligible_batting.apply(lambda r: f"pressure balls={int(r['pressure_balls'])}, pressure matches={int(r['pressure_matches'])}", axis=1)
    ineligible_bowling["reason"] = ineligible_bowling.apply(lambda r: f"pressure balls={int(r['pressure_balls'])}, pressure matches={int(r['pressure_matches'])}", axis=1)
    ineligible = pd.concat([ineligible_batting.assign(category="batting"), ineligible_bowling.assign(category="bowling")], ignore_index=True)

    return batting_rankings.head(10), bowling_rankings.head(10), ineligible, batting, bowling


def competition_comparison(batting_rankings: pd.DataFrame, bowling_rankings: pd.DataFrame):
    comp = pd.concat([
        batting_rankings.assign(category="batting")[['player_id','player_name','final_adjusted_score','category']],
        bowling_rankings.assign(category="bowling")[['player_id','player_name','final_adjusted_score','category']],
    ], ignore_index=True)
    return comp
