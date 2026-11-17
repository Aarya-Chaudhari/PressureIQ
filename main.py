from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import yaml

from src.data_cleaning import audit_datasets, build_data_dictionary, clean_core_tables, generate_data_quality_report
from src.match_state import reconstruct_match_state
from src.pressure_engine import compute_pressure_scores
from src.batting_analysis import batting_metrics
from src.bowling_analysis import bowling_metrics
from src.ranking_engine import apply_eligibility_and_rank, competition_comparison
from src.validation import sensitivity_analysis, validation_report_md, ranking_stability
from src.scouting import build_scouting_profiles
from src.report_generator import generate_exec_summary, generate_pdf_report


def load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_output_dir(path: str | Path):
    Path(path).mkdir(parents=True, exist_ok=True)


def main():
    root = Path(__file__).resolve().parent
    config = load_config(root / "config.yaml")
    raw_dir = root / config["project"]["data_dir"]
    output_dir = root / config["project"]["output_dir"]
    ensure_output_dir(output_dir)
    ensure_output_dir(output_dir / "charts")

    audit_df = audit_datasets(raw_dir, output_dir / "data_audit.csv")
    dictionary_df = build_data_dictionary(raw_dir, output_dir / "data_dictionary.csv")
    generate_data_quality_report(raw_dir, audit_df, output_dir / "data_quality_report.md")

    clean_df, matches_df, competitions_df, teams_df, player_map, playing_eleven = clean_core_tables(raw_dir)
    clean_df["season_year"] = clean_df["season"].astype(str).str.extract(r"(\d{4})").astype(float)
    filtered = clean_df[(clean_df["match_format"].isin(["T20I", "T20"])) & (clean_df["season_year"] >= 2022)].copy()
    processed = reconstruct_match_state(filtered, matches_df, competitions_df, output_dir / "processed_deliveries.csv")
    processed = compute_pressure_scores(processed, config)
    processed.to_csv(output_dir / "pressure_analysis.csv", index=False)

    batting_stats = batting_metrics(processed)
    bowling_stats = bowling_metrics(processed)
    batting_stats.to_csv(output_dir / "batting_player_statistics.csv", index=False)
    bowling_stats.to_csv(output_dir / "bowling_player_statistics.csv", index=False)

    batting_rankings, bowling_rankings, ineligible, batting_all, bowling_all = apply_eligibility_and_rank(batting_stats, bowling_stats, config)
    batting_rankings.to_csv(output_dir / "batting_rankings.csv", index=False)
    bowling_rankings.to_csv(output_dir / "bowling_rankings.csv", index=False)
    ineligible.to_csv(output_dir / "ineligible_players.csv", index=False)
    competition_comparison_df = competition_comparison(batting_rankings, bowling_rankings)
    competition_comparison_df.to_csv(output_dir / "competition_comparison.csv", index=False)

    sensitivity_df = sensitivity_analysis(batting_rankings, bowling_rankings)
    sensitivity_df.to_csv(output_dir / "sensitivity_analysis.csv", index=False)
    ranking_stability_df = ranking_stability(batting_rankings, bowling_rankings)
    ranking_stability_df.to_csv(output_dir / "ranking_stability.csv", index=False)
    validation_report_md(sensitivity_df, output_dir / "validation_report.md")

    build_scouting_profiles(batting_rankings.head(10), bowling_rankings.head(10), output_dir / "rr_scouting_recommendations.md")
    generate_exec_summary(output_dir / "EXECUTIVE_SUMMARY.md", batting_rankings.head(10), bowling_rankings.head(10))

    model_audit = """# Model Audit\n\n| Component | Existing implementation | Problem | Required correction |\n|---|---|---|---|\n| Pressure formula | Batting and bowling pressure are approximated from simplified score and time features. | The model does not fully reconstruct actual match-state requirements or use competition-aware baselines. | Use match-state reconstruction with required run rate, wickets remaining, balls remaining, and phase-specific pressure factors. |\n| Batting formula | Z-scores are computed on self-selected player groups with uneven comparisons. | Pressure and normal populations are not aligned to matching role and phase contexts. | Compare players within competition and innings-phase baselines with consistent reference populations. |\n| Bowling formula | Economy and wicket metrics are treated without strong normalization. | Wides, no-balls, non-bowler dismissals and phase differences are not fully separated. | Use legal-ball accounting, bowler-specific wicket attribution, and comparable competition-phase groups. |\n| Normal performance | Pressure and non-pressure groups are treated as separate but not standardised. | This can distort uplift and mis-rank players with small samples. | Keep a consistent baseline scale and apply shrinkage to avoid sample-driven overstatements. |\n| IPL/T20I handling | Competition scores are combined heuristically. | Missing T20I data should not be treated as zero performance. | Use sample-aware weighting, competition-specific baselines, and explicit coverage notes. |\n| Validation | Only simple threshold checks are run. | This does not test ranking stability or model sensitivity. | Run multi-threshold sensitivity and recording of ranking consistency. |\n"""
    (output_dir / "model_audit.md").write_text(model_audit, encoding="utf-8")

    # simple chart generation
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.hist(processed["batting_pressure_score"], bins=20, alpha=0.7, label="Batting")
    ax.hist(processed["bowling_pressure_score"], bins=20, alpha=0.6, label="Bowling")
    ax.set_title("Pressure score distribution")
    ax.set_xlabel("Pressure score")
    ax.set_ylabel("Delivery count")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "charts" / "pressure_score_distribution.png", dpi=200)
    plt.close(fig)

    # top 10 bar plots
    if not batting_rankings.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(batting_rankings["player_name"].head(10)[::-1], batting_rankings["final_adjusted_score"].head(10)[::-1], color="#d94d8f")
        ax.set_title("Top 10 batting pressure ratings")
        ax.set_xlabel("Adjusted score")
        ax.invert_yaxis()
        fig.tight_layout()
        fig.savefig(output_dir / "charts" / "top_batting_leaderboard.png", dpi=200)
        plt.close(fig)

    if not bowling_rankings.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(bowling_rankings["player_name"].head(10)[::-1], bowling_rankings["final_adjusted_score"].head(10)[::-1], color="#4aa3ff")
        ax.set_title("Top 10 bowling pressure ratings")
        ax.set_xlabel("Adjusted score")
        ax.invert_yaxis()
        fig.tight_layout()
        fig.savefig(output_dir / "charts" / "top_bowling_leaderboard.png", dpi=200)
        plt.close(fig)

    generate_pdf_report(output_dir / "PressureIQ_RR_Methodology_Report.pdf", batting_rankings.head(10), bowling_rankings.head(10), sensitivity_df)

    print(f"PressureIQ complete. Results saved in {output_dir}")


if __name__ == "__main__":
    main()
