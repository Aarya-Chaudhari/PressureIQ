import pandas as pd

from src.match_state import reconstruct_match_state


def test_legal_delivery_count_and_target_reconstruction():
    df = pd.DataFrame([
        {"match_id": 1, "innings": 1, "overid": 1, "over_ball_num": 1, "runs": 0, "is_wicket": False, "extras_type": None, "match_date": "2024-01-01", "batting_team_id": 10, "bowling_team_id": 20, "striker_id": 1, "striker_name": "A", "bowler_id": 2, "bowler_name": "B", "comp_id": 100, "match_format": "T20I", "season": 2024},
        {"match_id": 1, "innings": 1, "overid": 1, "over_ball_num": 2, "runs": 1, "is_wicket": False, "extras_type": None, "match_date": "2024-01-01", "batting_team_id": 10, "bowling_team_id": 20, "striker_id": 1, "striker_name": "A", "bowler_id": 2, "bowler_name": "B", "comp_id": 100, "match_format": "T20I", "season": 2024},
        {"match_id": 1, "innings": 2, "overid": 1, "over_ball_num": 1, "runs": 2, "is_wicket": False, "extras_type": None, "match_date": "2024-01-01", "batting_team_id": 20, "bowling_team_id": 10, "striker_id": 3, "striker_name": "C", "bowler_id": 4, "bowler_name": "D", "comp_id": 100, "match_format": "T20I", "season": 2024},
    ])
    matches = pd.DataFrame([{"match_id": 1, "comp_id": 100, "match_date": "2024-01-01", "revised_target": 150, "first_inn_revised_overs": 20, "second_inn_revised_overs": 20}])
    competitions = pd.DataFrame([{"comp_id": 100, "comp_name": "Test T20I", "match_format": "T20I", "season": 2024}])
    state = reconstruct_match_state(df, matches, competitions, "tmp.csv")
    assert bool(state.iloc[0]["legal_delivery"]) is True
    assert state.iloc[0]["score_before_delivery"] == 0
    assert state.iloc[1]["score_before_delivery"] == 0
    assert state.iloc[2]["target_score"] == 150
