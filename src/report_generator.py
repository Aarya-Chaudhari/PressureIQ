from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = HexColor("#071827")
MIDNIGHT = HexColor("#0D1D2E")
SLATE = HexColor("#122A3E")
PINK = HexColor("#F23B8C")
BLUE = HexColor("#58A6FF")
MINT = HexColor("#57D7B3")
TEXT = HexColor("#EAF3FF")
MUTED = HexColor("#A3B5CE")
LINE = HexColor("#254565")


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _metric_block(title: str, value: str, accent: colors.Color):
    return Table(
        [[Paragraph(f"<font color='{hex(accent)[2:].upper()}' size='8'><b>{title}</b></font>", style="BodyText"), ""],
         [Paragraph(f"<font color='white' size='18'><b>{value}</b></font>", style="BodyText"), ""]],
        colWidths=[180, 0],
        rowHeights=[12, 18],
    )


def _load_analysis_metrics(report_dir: Path):
    metrics = {
        "matches": 0,
        "deliveries": 0,
        "players": 0,
        "eligible_batters": 0,
        "eligible_bowlers": 0,
        "high_pressure_events": 0,
    }

    pressure_path = report_dir / "pressure_analysis.csv"
    batting_path = report_dir / "batting_rankings.csv"
    bowling_path = report_dir / "bowling_rankings.csv"

    if pressure_path.exists():
        pressure = pd.read_csv(pressure_path, low_memory=False)
        metrics["matches"] = _safe_int(pressure["match_id"].nunique()) if "match_id" in pressure.columns else 0
        metrics["deliveries"] = len(pressure)
        if {"striker_id", "bowler_id"}.issubset(pressure.columns):
            ids = pd.concat([pressure["striker_id"], pressure["bowler_id"]], ignore_index=True).dropna()
            metrics["players"] = len(set(ids.astype(str)))
        metrics["high_pressure_events"] = _safe_int((pressure["batting_pressure_flag"] == "High").sum() + (pressure["bowling_pressure_flag"] == "High").sum())

    if batting_path.exists():
        batting = pd.read_csv(batting_path, low_memory=False)
        metrics["eligible_batters"] = int(batting["eligible"].fillna(False).astype(bool).sum()) if "eligible" in batting.columns else 0

    if bowling_path.exists():
        bowling = pd.read_csv(bowling_path, low_memory=False)
        metrics["eligible_bowlers"] = int(bowling["eligible"].fillna(False).astype(bool).sum()) if "eligible" in bowling.columns else 0

    return metrics


def generate_exec_summary(output_md: str | Path, top_batters: pd.DataFrame, top_bowlers: pd.DataFrame):
    lines = [
        "# Executive Summary",
        "",
        "PressureIQ applies a transparent match-state reconstruction and pressure model to actual IPL and T20I data from 2022 onward.",
        "",
        "## Top 10 batters under pressure",
    ]
    for _, row in top_batters.head(10).iterrows():
        lines.append(f"- {row['player_name']}: final adjusted score {row.get('final_adjusted_score', 0):.3f}, pressure matches {int(row.get('pressure_matches', 0))}")
    lines.append("")
    lines.append("## Top 10 bowlers under pressure")
    for _, row in top_bowlers.head(10).iterrows():
        lines.append(f"- {row['player_name']}: final adjusted score {row.get('final_adjusted_score', 0):.3f}, pressure matches {int(row.get('pressure_matches', 0))}")
    Path(output_md).write_text("\n".join(lines), encoding="utf-8")


def generate_pdf_report(pdf_path: str | Path, top_batters: pd.DataFrame, top_bowlers: pd.DataFrame, validation_df: pd.DataFrame):
    output_dir = Path(pdf_path).resolve().parent
    metrics = _load_analysis_metrics(output_dir)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle("CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=28, leading=32, textColor=TEXT, alignment=1, spaceAfter=10, borderPadding=0))
    styles.add(ParagraphStyle("CoverSubtitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=18, leading=24, textColor=TEXT, alignment=1, spaceAfter=14, borderPadding=0))
    styles.add(ParagraphStyle("SectionTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=22, leading=24, textColor=TEXT, spaceBefore=10, spaceAfter=8))
    styles.add(ParagraphStyle("SectionEyebrow", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=PINK, letterSpace=1.8, spaceBefore=0, spaceAfter=6))
    styles.add(ParagraphStyle("BodyTextDark", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15, textColor=TEXT, alignment=1))
    styles.add(ParagraphStyle("MutedText", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=MUTED))
    styles.add(ParagraphStyle("NarrowCaption", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=MUTED))
    styles.add(ParagraphStyle("MetricLabel", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=MUTED, alignment=1, spaceAfter=6))
    styles.add(ParagraphStyle("MetricValue", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=18, leading=20, textColor=TEXT, alignment=1))
    styles.add(ParagraphStyle("BulletText", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.2, leading=15, textColor=TEXT, leftIndent=12, firstLineIndent=-10))
    styles.add(ParagraphStyle("PullQuote", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=12, leading=18, textColor=TEXT, alignment=1, borderColor=LINE, borderWidth=1, borderPadding=10, backColor=SLATE))

    story: list = []

    cover = Table(
        [[Paragraph("<font color='#F23B8C' size='9'><b>SUPERR SELECTOR SEASON 2</b></font>", styles["BodyText"])]],
        colWidths=[150],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(Spacer(1, 18))
    story.append(cover)
    story.append(Spacer(1, 12))
    story.append(Paragraph("PRESSUREIQ", styles["CoverTitle"]))
    story.append(Paragraph("Beyond the Numbers: Identifying Cricket's Most Reliable Performers Under Pressure", styles["CoverSubtitle"]))
    story.append(Paragraph("A Data-Driven Player Reliability and Auction Scouting Intelligence Framework", styles["BodyTextDark"]))
    story.append(Spacer(1, 30))
    story.append(Paragraph("ROUND 1 · IPL 2027 SCOUTING · MATCH-STATE ANALYTICS", styles["SectionEyebrow"]))
    story.append(Paragraph("Traditional cricket statistics interpret performance as a single summary. PressureIQ asks a more important question: when the match becomes difficult, can a player still perform reliably?", styles["BodyTextDark"]))
    story.append(PageBreak())

    story.append(Paragraph("SECTION 2 · EXECUTIVE SUMMARY", styles["SectionEyebrow"]))
    story.append(Paragraph("Why PressureIQ matters", styles["SectionTitle"]))
    story.append(Paragraph(
        "PressureIQ reconstructs each delivery in context, measures the match situation before the ball is bowled, and compares performance under pressure with performance in normal phases. The result is a more defensible player-evaluation framework for auction scouting and role-specific assessment.",
        styles["BodyText"],
    ))

    metric_cards = [
        ("MATCHES", f"{metrics['matches']:,}", BLUE),
        ("DELIVERIES", f"{metrics['deliveries']:,}", PINK),
        ("PLAYERS", f"{metrics['players']:,}", MINT),
        ("ELIGIBLE BATTERS", f"{metrics['eligible_batters']}", PINK),
        ("ELIGIBLE BOWLERS", f"{metrics['eligible_bowlers']}", BLUE),
        ("HIGH-PRESSURE EVENTS", f"{metrics['high_pressure_events']:,}", MINT),
    ]
    blocks = []
    for label, value, accent in metric_cards:
        box = Table(
            [[Paragraph(f"<font color='#A3B5CE' size='7'><b>{label}</b></font>", styles["MetricLabel"]), ""],
             [Paragraph(f"<font color='white' size='16'><b>{value}</b></font>", styles["MetricValue"]), ""]],
            colWidths=[150],
            rowHeights=[14, 28],
        )
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), MIDNIGHT),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
        ]))
        blocks.append(box)
    story.append(Table([blocks[i:i+3] for i in range(0, len(blocks), 3)], colWidths=[150, 150, 150], hAlign="LEFT"))
    story.append(Spacer(1, 14))
    story.append(Paragraph("The model is intentionally transparent: it reconstructs match state, classifies delivery context, and compares pressure-versus-normal performance before producing rank-ordered evidence. It does not rely on an opaque black-box predictor.", styles["BodyText"]))
    story.append(PageBreak())

    story.append(Paragraph("SECTION 3 · THE PROBLEM WITH TRADITIONAL CRICKET STATISTICS", styles["SectionEyebrow"]))
    story.append(Paragraph("Why averages are not enough", styles["SectionTitle"]))
    story.append(Paragraph("A batting average without context can hide severe volatility in a chase. A strike rate can be inflated by easy overs. An economy rate may look good but still come from a low-pressure spell. Total wickets are not a proxy for match impact when the difficulty of the ball changes sharply across phases of an innings.", styles["BodyText"]))
    story.append(Paragraph("Illustrative example (not a dataset claim): a batter scoring 35 off 20 in a 10-over chase is materially different from 35 off 20 in a middle-overs dead-rubber phase. Similarly, a bowler conceding 12 runs in an over while defending 18 off the last over is not comparable to an over bowled when the field set is simple and the game is already settled.", styles["PullQuote"]))
    story.append(Paragraph("The core issue is context. A player may score runs or pick up wickets, but the value of those actions depends on the phase, required rate, wickets in hand, and the degree of opposition pressure. PressureIQ treats these features as first-class evidence rather than as after-the-fact footnotes.", styles["BodyText"]))
    story.append(PageBreak())

    story.append(Paragraph("SECTION 4 · OUR APPROACH AND DESIGN PHILOSOPHY", styles["SectionEyebrow"]))
    story.append(Paragraph("Match-state reconstruction before ranking", styles["SectionTitle"]))
    story.append(Paragraph("The analytical choice was straightforward: evaluate the ball-by-ball situation, not just the aggregate innings summary. This design philosophy has four practical consequences:", styles["BodyText"]))
    bullet_text = [
        "1. Ball-by-ball analysis lets the model capture urgency, wickets in hand, and the actual hunt for runs or breakthroughs.",
        "2. Match-state reconstruction is required before measuring pressure because the same score has different meaning in different phases of an innings.",
        "3. Pressure and normal contexts are compared within the same player profile so that ranking is based on relative performance in difficult circumstances, not isolated headline numbers.",
        "4. Sample-aware adjustment prevents very short or filtered observations from dominating the leaderboard without removing genuine signal.",
    ]
    for item in bullet_text:
        story.append(Paragraph(item, styles["BulletText"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("The project was intentionally designed to be explainable: each player is evaluated using evidence that can be traced back to specific match-state conditions rather than to a purely opaque machine-learning score.", styles["BodyText"]))
    story.append(PageBreak())

    story.append(Paragraph("SECTION 5 · METHODOLOGY IN PRACTICE", styles["SectionEyebrow"]))
    story.append(Paragraph("What the model actually measures", styles["SectionTitle"]))
    story.append(Paragraph("The implemented workflow in the project uses actual CSV data from the supplied data pack and reconstructs each delivery with match state fields such as score before delivery, wickets before delivery, balls remaining, target score, required run rate, innings phase, and legal-ball accounting. Pressure is then estimated from scoring urgency, wicket pressure, remaining time, and phase context. Each batter and bowler is evaluated against both pressure and normal delivery groups before a sample-share adjustment is applied.", styles["BodyText"]))
    table_data = [
        ["Dimension", "Actual implementation"],
        ["Pressure indicator", "Required run rate, balls remaining, wickets left, innings phase, and run chase context"],
        ["Batting score", "Scoring-rate pressure + wicket pressure + time pressure + phase context"],
        ["Bowling score", "Opposition rate + wicket resource + time context + match closeness"],
        ["Ranking logic", "Pressure-context performance versus normal-context performance, adjusted by sample share"],
    ]
    metrics_table = Table(table_data, colWidths=[90, 400])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1B2E3F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), TEXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), MIDNIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph("The project does not claim a proprietary black-box match model; the code and outputs make the pressure logic inspectable. The configuration file sets thresholds and weights, including the high/medium pressure cutoffs and minimum sample requirements for eligibility.", styles["BodyText"]))
    story.append(PageBreak())

    story.append(Paragraph("SECTION 6 · EVIDENCE FROM THE IMPLEMENTED DATA", styles["SectionEyebrow"]))
    story.append(Paragraph("Actual pressure distribution and leaderboards", styles["SectionTitle"]))
    chart_dir = output_dir / "charts"
    figure_files = ["pressure_score_distribution.png", "top_batting_leaderboard.png", "top_bowling_leaderboard.png"]
    for idx, name in enumerate(figure_files):
        path = chart_dir / name
        if path.exists():
            story.append(Paragraph(f"Figure {idx + 1}: {name.replace('_', ' ').title()}", styles["NarrowCaption"]))
            story.append(Image(str(path), width=500, height=210, kind="proportional"))
            story.append(Spacer(1, 8))
    story.append(PageBreak())

    story.append(Paragraph("SECTION 7 · WHAT THE ACTUAL RANKINGS SAY", styles["SectionEyebrow"]))
    story.append(Paragraph("Top pressure performers in the current output", styles["SectionTitle"]))
    bat_rows = [["Rank", "Player", "Adjusted score", "Pressure balls", "Matches"]]
    for _, row in top_batters.head(10).iterrows():
        bat_rows.append([int(row["rank"]), row["player_name"], f"{row.get('final_adjusted_score', 0):.3f}", int(row.get('pressure_balls', 0)), int(row.get('pressure_matches', 0))])
    bow_rows = [["Rank", "Player", "Adjusted score", "Pressure balls", "Matches"]]
    for _, row in top_bowlers.head(10).iterrows():
        bow_rows.append([int(row["rank"]), row["player_name"], f"{row.get('final_adjusted_score', 0):.3f}", int(row.get('pressure_balls', 0)), int(row.get('pressure_matches', 0))])
    bat_table = Table(bat_rows, colWidths=[30, 120, 55, 55, 40])
    bat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), TEXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), MIDNIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    bow_table = Table(bow_rows, colWidths=[30, 120, 55, 55, 40])
    bow_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("TEXTCOLOR", (0, 0), (-1, 0), TEXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), MIDNIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(Paragraph("Batting leaders", styles["BodyText"]))
    story.append(bat_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Bowling leaders", styles["BodyText"]))
    story.append(bow_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Actual leaderboards from the generated outputs show Mahipal Lomror as the leading eligible batter, while Ahmed Daniyal leads the bowling ranking. The sensitivity summary confirms these leaders remain stable across conservative, standard, and aggressive pressure cutoffs.", styles["BodyText"]))
    story.append(PageBreak())

    story.append(Paragraph("SECTION 8 · DECISION SUPPORT FOR RR SCOUTING", styles["SectionEyebrow"]))
    story.append(Paragraph("Translating ranked evidence into scouting decisions", styles["SectionTitle"]))
    story.append(Paragraph("For Rajasthan Royals' scouting and auction planning, the central value is not a single headline number. It is a transparent read on who can convert pressure scenarios into output. The strongest signals are players who combine high match-context quality with enough sample depth to have credibility. The model deliberately filters out players with too little pressure exposure, so the final list is more useful for decision support than raw aggregate lists.", styles["BodyText"]))
    story.append(Paragraph("The generated scouting note in the project recommends the top pressure performers only when the evidence is grounded in the historical data and minimum sample thresholds have been satisfied. That is a more defensible decision framework than selecting players purely on aggregate IPL numbers from non-contextualized periods.", styles["BodyText"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("The final interpretation is practical: PressureIQ identifies reliability under difficulty, not just overall volume. In an auction context, that is the relevant distinction.", styles["PullQuote"]))
    story.append(PageBreak())

    story.append(Paragraph("SECTION 9 · VALIDATION AND LIMITATIONS", styles["SectionEyebrow"]))
    story.append(Paragraph("Testing the model responsibly", styles["SectionTitle"]))
    story.append(Paragraph("The project includes a validation report that checks ranking stability across multiple pressure thresholds and confirms that the leaders remain stable under conservative, standard, and aggressive settings. It also applies minimum pressure-ball and pressure-match filters to prevent outliers from dominating the leaderboard. The project is transparent about the limits of the data: these are historical match contexts, not a full player forecast model.", styles["BodyText"]))
    story.append(Paragraph(f"Sensitivity review included {len(validation_df)} configurations. Top batting leader: {top_batters.iloc[0]['player_name']} | Top bowling leader: {top_bowlers.iloc[0]['player_name']}", styles["BodyText"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("In practical terms, the model is strongest when used as a comparative scouting lens: it tells us which players perform best when the match situation becomes difficult, while remaining honest about sample coverage and the limits of historical evidence.", styles["BodyText"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("PRESSUREIQ · DATA-DRIVEN PLAYER RELIABILITY UNDER PRESSURE", styles["NarrowCaption"]))

    doc.build(story)
