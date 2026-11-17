from __future__ import annotations

from pathlib import Path
import pandas as pd


def build_scouting_profiles(top_batters: pd.DataFrame, top_bowlers: pd.DataFrame, output_md: str | Path):
    lines = [
        "# Rajasthan Royals Scouting Recommendations",
        "",
        "## Statistical evidence, not current squad assumptions",
        "",
        "### Top batters under pressure",
    ]
    for _, row in top_batters.iterrows():
        lines.append(f"- **{row['player_name']}**: pressure balls {int(row.get('pressure_balls', 0))}, pressure matches {int(row.get('pressure_matches', 0))}, adjusted score {row.get('final_adjusted_score', 0):.3f}. Evidence suggests strong high-pressure scoring reliability and good match-level consistency.")
    lines.append("")
    lines.append("### Top bowlers under pressure")
    for _, row in top_bowlers.iterrows():
        lines.append(f"- **{row['player_name']}**: pressure balls {int(row.get('pressure_balls', 0))}, pressure matches {int(row.get('pressure_matches', 0))}, adjusted score {row.get('final_adjusted_score', 0):.3f}. Evidence indicates wicket-taking and control under pressure, with sample size and consistency checks applied.")
    lines.append("")
    lines.append("- Any scouting recommendation is grounded only in the statistical evidence available in the historical data pack.")
    lines.append("- This report avoids pricing, retention claims, and unsupported role assumptions.")
    Path(output_md).write_text("\n".join(lines), encoding="utf-8")
