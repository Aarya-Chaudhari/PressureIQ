# Data Quality Report

- Files audited: 6
- Total rows: 237170
- Total missing values: 795214

## Audit Highlights

- **ball_by_ball.csv**: 200999 rows, 33 columns, 0 duplicate rows.
- **competition_team_player_mapping.csv**: 6413 rows, 6 columns, 0 duplicate rows.
- **competitions.csv**: 141 rows, 4 columns, 0 duplicate rows.
- **matches.csv**: 883 rows, 22 columns, 0 duplicate rows.
- **playing_eleven.csv**: 28381 rows, 9 columns, 0 duplicate rows.
- **teams.csv**: 353 rows, 3 columns, 0 duplicate rows.

## Data quality notes
- Raw CSV files were inspected without modification.
- Player identities are recovered from competition_team_player_mapping and playing_eleven tables, not from a standalone player registry.
- Match state is reconstructed from ball-by-ball sequence order and competition metadata.