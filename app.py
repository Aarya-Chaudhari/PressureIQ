from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
PINK = "#F23B8C"
BLUE = "#58A6FF"
MINT = "#57D7B3"
MUTED = "#91A3BC"

st.set_page_config(
    page_title="PressureIQ | Player intelligence",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="Loading PressureIQ data…")
def read_output(name: str) -> pd.DataFrame:
    path = OUTPUTS / name
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def load_data() -> dict[str, pd.DataFrame]:
    return {
        "batting": read_output("batting_rankings.csv"),
        "bowling": read_output("bowling_rankings.csv"),
        "pressure": read_output("pressure_analysis.csv"),
        "sensitivity": read_output("sensitivity_analysis.csv"),
        "stability": read_output("ranking_stability.csv"),
    }


def competition_label(value: object) -> str:
    name = str(value).lower()
    return "IPL" if "ipl" in name else "T20I"


def style_plot(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, sans-serif", "color": "#D8E2F0", "size": 12},
        title={"font": {"size": 16, "color": "#F4F7FC"}, "x": 0.02},
        margin={"l": 18, "r": 18, "t": 55, "b": 24},
        legend={"bgcolor": "rgba(0,0,0,0)", "orientation": "h", "y": 1.12, "x": 0},
    )
    fig.update_xaxes(gridcolor="rgba(145,163,188,.12)", zerolinecolor="rgba(145,163,188,.15)")
    fig.update_yaxes(gridcolor="rgba(145,163,188,.12)", zerolinecolor="rgba(145,163,188,.15)")
    return fig


def section_heading(eyebrow: str, title: str, caption: str = "") -> None:
    st.markdown(
        f"""<div class="section-head">
        <div class="eyebrow">{eyebrow}</div><h2>{title}</h2>
        <div class="section-caption">{caption}</div></div>""",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, detail: str, accent: str) -> None:
    st.markdown(
        f"""<div class="metric-card" style="--accent:{accent}">
        <div class="metric-label">{label}</div><div class="metric-value">{value}</div>
        <div class="metric-detail">{detail}</div></div>""",
        unsafe_allow_html=True,
    )


def player_table(df: pd.DataFrame, mode: str) -> None:
    if df.empty:
        st.info("No players meet the current eligibility criteria.")
        return
    if mode == "batting":
        wanted = [
            ("rank", "RANK"), ("player_name", "PLAYER"), ("final_adjusted_score", "SCORE"),
            ("strike_rate", "OVERALL SR"), ("pressure_balls", "PRESSURE BALLS"),
            ("pressure_matches", "MATCHES"), ("batting_uplift", "UPLIFT"),
        ]
    else:
        wanted = [
            ("rank", "RANK"), ("player_name", "PLAYER"), ("final_adjusted_score", "SCORE"),
            ("economy", "ECONOMY"), ("wicket_rate", "WICKETS / 6"),
            ("pressure_balls", "PRESSURE BALLS"), ("pressure_matches", "MATCHES"),
        ]
    present = [(key, label) for key, label in wanted if key in df.columns]
    display = df[[key for key, _ in present]].copy()
    display.columns = [label for _, label in present]
    formats = {column: "{:.2f}" for column in ("SCORE", "OVERALL SR", "UPLIFT", "ECONOMY", "WICKETS / 6") if column in display.columns}
    st.dataframe(
        display.style.format(formats),
        use_container_width=True,
        hide_index=True,
        height=min(460, 45 + len(display) * 38),
    )


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root { --ink:#F4F7FC; --muted:#91A3BC; --pink:#F23B8C; --blue:#58A6FF; --line:rgba(143,164,193,.16); }
    html, body, [class*="css"] { font-family: 'Manrope', 'Segoe UI', sans-serif; }
    .stApp { background: radial-gradient(ellipse at 72% -18%, rgba(52,92,151,.23), transparent 42%),
      radial-gradient(ellipse at -15% 28%, rgba(242,59,140,.10), transparent 36%), #07111F; color:var(--ink); }
    [data-testid="stHeader"] { background:rgba(7,17,31,.7); }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#0C1929 0%,#091522 100%); border-right:1px solid var(--line); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .3rem .1rem; }
    .block-container { max-width:1440px; padding:2rem 2.4rem 3rem; }
    h1,h2,h3 { letter-spacing:-.04em; color:var(--ink); }
    .brand { padding:1.15rem 1rem 1.25rem; border:1px solid var(--line); border-radius:18px;
      background:linear-gradient(135deg,rgba(242,59,140,.13),rgba(88,166,255,.07)); margin-bottom:1.35rem; }
    .brand-mark { display:flex; align-items:center; gap:.7rem; font-size:1.22rem; font-weight:800; letter-spacing:.13em; }
    .brand-icon { display:inline-grid; place-items:center; width:34px; height:34px; border-radius:11px;
      background:linear-gradient(135deg,var(--pink),#8D55E8); color:white; }
    .brand-sub { color:var(--muted); font-size:.72rem; line-height:1.5; margin:.65rem 0 0; }
    .hero { position:relative; overflow:hidden; padding:2.1rem 2.3rem; border-radius:22px; margin:.25rem 0 1.6rem;
      border:1px solid rgba(115,159,224,.22);
      background:linear-gradient(112deg,rgba(17,39,66,.98) 0%,rgba(16,35,60,.94) 56%,rgba(73,24,66,.65) 100%); }
    .hero:after { content:' '; position:absolute; width:240px;height:240px;right:-45px;top:-105px;border:1px solid rgba(242,59,140,.22);
      border-radius:50%;box-shadow:0 0 0 28px rgba(242,59,140,.035),0 0 0 58px rgba(88,166,255,.025); }
    .hero-kicker,.eyebrow { color:#F67EB1; font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:.14em; font-size:.68rem; }
    .hero h1 { font-size:clamp(2rem,4vw,3.55rem); line-height:1.05; margin:.7rem 0 .55rem; font-weight:800; }
    .hero p { color:#B6C5D8; max-width:700px; font-size:.97rem; line-height:1.7; margin:0; }
    .hero-chip { display:inline-block; margin-top:1.15rem; padding:.45rem .7rem; border-radius:99px; color:#D9E7F7;
      border:1px solid rgba(160,188,222,.2); background:rgba(4,14,26,.36); font-size:.72rem; }
    .metric-card { height:128px; padding:1.08rem 1.1rem; border:1px solid var(--line); border-radius:16px;
      background:linear-gradient(150deg,rgba(19,38,61,.96),rgba(12,26,43,.9)); box-shadow:0 10px 24px rgba(0,0,0,.12);
      border-top:2px solid var(--accent); }
    .metric-label { color:var(--muted); font-size:.7rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
    .metric-value { margin:.48rem 0 .1rem; color:#F7F9FD; font-size:1.8rem; font-weight:800; letter-spacing:-.06em; }
    .metric-detail { color:#71849D; font-size:.68rem; }
    .section-head { margin:2rem 0 1rem; }
    .section-head h2 { font-size:1.5rem; margin:.35rem 0 .2rem; }
    .section-caption { color:var(--muted); font-size:.82rem; }
    .panel { padding:1.1rem 1.15rem; border:1px solid var(--line); border-radius:17px;
      background:rgba(14,29,47,.76); }
    .stTabs [data-baseweb="tab-list"] { gap:.4rem; border-bottom:1px solid var(--line); }
    .stTabs [data-baseweb="tab"] { color:#A9B8CC; border-radius:9px 9px 0 0; }
    .stTabs [aria-selected="true"] { color:white !important; border-bottom-color:var(--pink) !important; }
    [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:13px; overflow:hidden; }
    div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label { color:#A9B8CC; }
    .small-note { color:#788BA3; font-size:.74rem; }
    hr { border-color:var(--line); }
    footer { visibility:hidden; }
    @media(max-width:700px) { .block-container{padding:1rem .85rem 2rem;} .hero{padding:1.5rem;} .metric-card{height:112px;} }
    </style>
    """,
    unsafe_allow_html=True,
)

data = load_data()
batting = data["batting"]
bowling = data["bowling"]
pressure = data["pressure"]

with st.sidebar:
    st.markdown(
        """<div class="brand"><div class="brand-mark"><span class="brand-icon">P</span> PRESSUREIQ</div>
        <div class="brand-sub">PLAYER INTELLIGENCE<br>RAJASTHAN ROYALS · IPL 2027</div></div>""",
        unsafe_allow_html=True,
    )
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Batting", "Bowling", "Player profile", "Pressure lab", "Model validation", "Scouting room", "Methodology"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("DATA COVERAGE")
    comp_filter = st.selectbox("Competition", ["All", "IPL", "T20I"])
    if not pressure.empty and "season" in pressure.columns:
        seasons = sorted(pressure["season"].dropna().astype(str).unique().tolist())
    else:
        seasons = []
    season_filter = st.selectbox("Season", ["All"] + seasons)
    st.markdown("---")
    st.markdown('<div class="small-note">Match-state model · Ball-by-ball evidence<br>Model build 2.0</div>', unsafe_allow_html=True)

filtered_pressure = pressure.copy()
if not filtered_pressure.empty:
    if comp_filter != "All" and "competition" in filtered_pressure.columns:
        filtered_pressure = filtered_pressure[
            filtered_pressure["competition"].map(competition_label) == comp_filter
        ]
    if season_filter != "All" and "season" in filtered_pressure.columns:
        filtered_pressure = filtered_pressure[filtered_pressure["season"].astype(str) == season_filter]

players_count = 0
if not pressure.empty:
    player_ids = pd.concat(
        [pressure.get("striker_id", pd.Series(dtype=object)), pressure.get("bowler_id", pd.Series(dtype=object))]
    ).dropna().nunique()
    players_count = int(player_ids)
eligible_batters = int(batting["eligible"].fillna(False).astype(bool).sum()) if "eligible" in batting else len(batting)
eligible_bowlers = int(bowling["eligible"].fillna(False).astype(bool).sum()) if "eligible" in bowling else len(bowling)


if page == "Overview":
    st.markdown(
        """<div class="hero"><div class="hero-kicker">HIGH-PRESSURE PLAYER INTELLIGENCE</div>
        <h1>Find the players<br>who deliver when it matters.</h1>
        <p>Evidence-led scouting intelligence from real IPL and T20I match situations. Explore pressure performance, compare player profiles, and inspect the model behind every ranking.</p>
        <span class="hero-chip">IPL + T20I &nbsp;·&nbsp; 2022 onward &nbsp;·&nbsp; Ball-by-ball analysis</span></div>""",
        unsafe_allow_html=True,
    )
    if pressure.empty:
        st.error("Pressure analysis data is missing. Run `python main.py` in the project folder to build dashboard outputs.")
    else:
        pressure_deliveries = int(
            (filtered_pressure["batting_pressure_flag"] == "High").sum()
            + (filtered_pressure["bowling_pressure_flag"] == "High").sum()
        )
        metrics = [
            ("MATCHES", f"{filtered_pressure['match_id'].nunique():,}", "In selected coverage", BLUE),
            ("DELIVERIES", f"{len(filtered_pressure):,}", "Observed ball-by-ball", PINK),
            ("PLAYERS", f"{players_count:,}", "Across batting + bowling", MINT),
            ("ELIGIBLE BATTERS", f"{eligible_batters:,}", "Passed sample thresholds", PINK),
            ("ELIGIBLE BOWLERS", f"{eligible_bowlers:,}", "Passed sample thresholds", BLUE),
            ("HIGH-PRESSURE EVENTS", f"{pressure_deliveries:,}", "Batting + bowling contexts", MINT),
        ]
        cols = st.columns(3)
        for i, item in enumerate(metrics):
            with cols[i % 3]:
                metric_card(*item)
        section_heading("THE LEADERBOARD", "Pressure performers", "Top-ranked eligible players from the generated analysis.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("#### Batting")
            player_table(batting, "batting")
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("#### Bowling")
            player_table(bowling, "bowling")
            st.markdown("</div>", unsafe_allow_html=True)
        if "competition" in filtered_pressure.columns:
            comp_counts = filtered_pressure.assign(format=filtered_pressure["competition"].map(competition_label)).groupby("format").size().reset_index(name="deliveries")
            fig = px.pie(comp_counts, names="format", values="deliveries", hole=.72, title="Analysis coverage")
            fig.update_traces(marker_colors=[PINK, BLUE], textinfo="label+percent")
            st.plotly_chart(style_plot(fig, 310), use_container_width=True)

elif page in ("Batting", "Bowling"):
    is_batting = page == "Batting"
    df = batting.copy() if is_batting else bowling.copy()
    title = "Batting under pressure" if is_batting else "Bowling under pressure"
    section_heading("PLAYER RANKINGS", title, "Ranked by the model's sample-adjusted score. Search and inspect the evidence behind each player.")
    if df.empty:
        st.error(f"{page} leaderboard is missing. Run `python main.py` to generate it.")
    else:
        q = st.text_input("Search player", placeholder="Type a player name…", key=f"{page}_search")
        if q:
            df = df[df["player_name"].astype(str).str.contains(q, case=False, na=False)]
        if is_batting and {"strike_rate", "pressure_balls"}.issubset(df.columns):
            metric_card("TOP PRESSURE SCORE", f"{df.iloc[0]['final_adjusted_score']:.3f}" if not df.empty else "—", "Adjusted batting score", PINK)
            chart = px.scatter(df, x="pressure_balls", y="final_adjusted_score", color="strike_rate", size="pressure_matches",
                               hover_name="player_name", color_continuous_scale=["#345778", PINK], title="Sample size and adjusted batting score")
        else:
            chart = px.scatter(df, x="pressure_balls", y="final_adjusted_score", color="economy", size="pressure_matches",
                               hover_name="player_name", color_continuous_scale=["#345778", BLUE], title="Sample size and adjusted bowling score")
        st.plotly_chart(style_plot(chart, 350), use_container_width=True)
        player_table(df, "batting" if is_batting else "bowling")

elif page == "Player profile":
    section_heading("PLAYER INTELLIGENCE", "A closer look at performance", "Compare pressure and normal contexts across the available ball-by-ball record.")
    if batting.empty and bowling.empty:
        st.error("Leaderboard data is missing. Run `python main.py` first.")
    else:
        all_names = sorted(set(batting.get("player_name", pd.Series(dtype=str)).dropna()) | set(bowling.get("player_name", pd.Series(dtype=str)).dropna()))
        name = st.selectbox("Select a ranked player", all_names)
        bat_row = batting[batting["player_name"] == name] if "player_name" in batting else pd.DataFrame()
        bowl_row = bowling[bowling["player_name"] == name] if "player_name" in bowling else pd.DataFrame()
        a, b, c = st.columns(3)
        a.metric("PLAYER", name)
        a_row = bat_row.iloc[0] if not bat_row.empty else None
        b_row = bowl_row.iloc[0] if not bowl_row.empty else None
        b.metric("BATTING SCORE", f"{a_row['final_adjusted_score']:.3f}" if a_row is not None else "—")
        c.metric("BOWLING SCORE", f"{b_row['final_adjusted_score']:.3f}" if b_row is not None else "—")
        if a_row is not None:
            st.markdown("#### Batting record")
            st.dataframe(bat_row, hide_index=True, use_container_width=True)
        if b_row is not None:
            st.markdown("#### Bowling record")
            st.dataframe(bowl_row, hide_index=True, use_container_width=True)
        if not pressure.empty:
            player_id = a_row["player_id"] if a_row is not None else b_row["player_id"]
            player_deliveries = pressure[
                (pressure.get("striker_id", pd.Series(index=pressure.index)).astype(str) == str(player_id))
                | (pressure.get("bowler_id", pd.Series(index=pressure.index)).astype(str) == str(player_id))
            ].copy()
            if not player_deliveries.empty:
                player_deliveries["match_date"] = pd.to_datetime(player_deliveries.get("match_date"), errors="coerce")
                if a_row is not None:
                    metric_col, flag_col = "batting_pressure_score", "batting_pressure_flag"
                else:
                    metric_col, flag_col = "bowling_pressure_score", "bowling_pressure_flag"
                player_deliveries["context"] = player_deliveries[flag_col].fillna("Unknown")
                fig = px.box(player_deliveries, x="context", y=metric_col, color="context",
                             color_discrete_map={"High": PINK, "Medium": BLUE, "Normal": "#687B94"},
                             title="Pressure context distribution")
                st.plotly_chart(style_plot(fig, 350), use_container_width=True)

elif page == "Pressure lab":
    section_heading("MATCH STATE", "Pressure lab", "Inspect how modeled pressure varies by innings phase and competition.")
    if filtered_pressure.empty:
        st.warning("No pressure records are available for the selected filters.")
    else:
        left, right = st.columns(2)
        with left:
            fig = px.histogram(filtered_pressure, x="batting_pressure_score", color="batting_pressure_flag",
                               nbins=28, barmode="overlay", opacity=.82,
                               color_discrete_map={"High": PINK, "Medium": BLUE, "Normal": "#60758F"},
                               title="Batting pressure distribution")
            st.plotly_chart(style_plot(fig), use_container_width=True)
        with right:
            fig = px.histogram(filtered_pressure, x="bowling_pressure_score", color="bowling_pressure_flag",
                               nbins=28, barmode="overlay", opacity=.82,
                               color_discrete_map={"High": PINK, "Medium": BLUE, "Normal": "#60758F"},
                               title="Bowling pressure distribution")
            st.plotly_chart(style_plot(fig), use_container_width=True)
        phase = filtered_pressure.groupby("innings_phase", dropna=False).agg(
            batting=("batting_pressure_score", "mean"), bowling=("bowling_pressure_score", "mean"), events=("match_id", "size")
        ).reset_index()
        phase_long = phase.melt(id_vars=["innings_phase", "events"], value_vars=["batting", "bowling"], var_name="role", value_name="mean score")
        fig = px.bar(phase_long, x="innings_phase", y="mean score", color="role", barmode="group",
                     color_discrete_map={"batting": PINK, "bowling": BLUE}, title="Average pressure score by innings phase",
                     hover_data=["events"])
        st.plotly_chart(style_plot(fig), use_container_width=True)
        if "required_run_rate" in filtered_pressure.columns:
            chase = filtered_pressure.dropna(subset=["required_run_rate"])
            if not chase.empty:
                fig = px.scatter(chase.sample(min(len(chase), 12000), random_state=7), x="required_run_rate",
                                 y="batting_pressure_score", color="wickets_remaining", opacity=.55,
                                 color_continuous_scale=["#EF5B9B", "#58A6FF"], title="Chase urgency and batting pressure")
                st.plotly_chart(style_plot(fig), use_container_width=True)

elif page == "Model validation":
    section_heading("MODEL CHECKS", "Validation & robustness", "Review the available sensitivity outputs and pressure-sample depth.")
    stability, sensitivity = data["stability"], data["sensitivity"]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Sensitivity scenarios")
        if sensitivity.empty:
            st.info("Sensitivity analysis file is not available.")
        else:
            st.dataframe(sensitivity, hide_index=True, use_container_width=True)
    with c2:
        st.markdown("#### Current ranking stability")
        if stability.empty:
            st.info("Ranking stability file is not available.")
        else:
            st.dataframe(stability, hide_index=True, use_container_width=True)
    if not batting.empty or not bowling.empty:
        combined = pd.concat([
            batting.assign(category="Batting"),
            bowling.assign(category="Bowling"),
        ], ignore_index=True)
        if {"pressure_balls", "final_adjusted_score", "player_name"}.issubset(combined.columns):
            fig = px.scatter(combined, x="pressure_balls", y="final_adjusted_score", color="category",
                             hover_name="player_name", color_discrete_map={"Batting": PINK, "Bowling": BLUE},
                             title="Pressure sample size vs. adjusted rating")
            st.plotly_chart(style_plot(fig), use_container_width=True)

elif page == "Scouting room":
    section_heading("RR SCOUTING ROOM", "Players to investigate", "Statistical evidence to support scouting review—not claims about availability or contract status.")
    tab_bat, tab_bowl = st.tabs(["BATTERS", "BOWLERS"])
    with tab_bat:
        player_table(batting, "batting")
        st.caption("Interpret scores alongside role, competition coverage, match consistency and video scouting.")
    with tab_bowl:
        player_table(bowling, "bowling")
        st.caption("Economy and wicket rates are sample-sensitive; validate role and phase fit before drawing conclusions.")
    report_path = OUTPUTS / "rr_scouting_recommendations.md"
    if report_path.exists():
        with st.expander("Open generated scouting notes"):
            st.markdown(report_path.read_text(encoding="utf-8"))

elif page == "Methodology":
    section_heading("TRANSPARENT BY DESIGN", "How PressureIQ works", "The model should explain the ranking—not hide behind it.")
    left, right = st.columns(2)
    with left:
        st.markdown(
            """<div class="panel"><div class="eyebrow">01 · PRESSURE</div><h3>Match situation first</h3>
            <p class="small-note">Pressure is measured before each ball using scoring urgency, wickets available, time remaining and innings context. A late over alone does not make an event high pressure.</p>
            <p><b>Batting:</b> 35% scoring-rate pressure · 25% wicket pressure · 25% time pressure · 15% phase context</p>
            <p><b>Bowling:</b> 35% opposition urgency · 25% wicket resources · 25% time · 15% closeness</p></div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            """<div class="panel"><div class="eyebrow">02 · BATTERS</div><h3>Pressure quality</h3>
            <p class="small-note">BPQ combines standardised strike rate, boundary rate, dot-ball rate and dismissal rate. Pressure uplift compares pressure quality with normal quality.</p>
            <p><code>Raw = 0.70 × Pressure BPQ − 0.30 × Uplift</code></p></div>""",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """<div class="panel"><div class="eyebrow">03 · BOWLERS</div><h3>Control and impact</h3>
            <p class="small-note">Bowling quality rewards wicket rate and dots while penalising economy and boundary concessions. Run-outs and other non-bowler dismissals should not earn bowler wickets.</p>
            <p><code>Raw = 0.70 × Pressure Quality − 0.30 × Uplift</code></p></div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            """<div class="panel"><div class="eyebrow">04 · FAIRNESS</div><h3>Sample-aware evidence</h3>
            <p class="small-note">Minimum pressure opportunities and match counts gate eligibility. Shrinkage reduces the influence of smaller samples; competition and phase coverage should be reviewed before comparison.</p>
            <p><b>Coverage:</b> supplied IPL and T20I records from 2022 onward.</p></div>""",
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown(
    '<div class="small-note">PRESSUREIQ · SCOUTING INTELLIGENCE &nbsp; / &nbsp; Values shown are generated from the local analysis outputs. Interpret rankings with sample size and methodology limitations in view.</div>',
    unsafe_allow_html=True,
)
