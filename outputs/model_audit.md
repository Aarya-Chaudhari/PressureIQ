# Model Audit

| Component | Existing implementation | Problem | Required correction |
|---|---|---|---|
| Pressure formula | Batting and bowling pressure are approximated from simplified score and time features. | The model does not fully reconstruct actual match-state requirements or use competition-aware baselines. | Use match-state reconstruction with required run rate, wickets remaining, balls remaining, and phase-specific pressure factors. |
| Batting formula | Z-scores are computed on self-selected player groups with uneven comparisons. | Pressure and normal populations are not aligned to matching role and phase contexts. | Compare players within competition and innings-phase baselines with consistent reference populations. |
| Bowling formula | Economy and wicket metrics are treated without strong normalization. | Wides, no-balls, non-bowler dismissals and phase differences are not fully separated. | Use legal-ball accounting, bowler-specific wicket attribution, and comparable competition-phase groups. |
| Normal performance | Pressure and non-pressure groups are treated as separate but not standardised. | This can distort uplift and mis-rank players with small samples. | Keep a consistent baseline scale and apply shrinkage to avoid sample-driven overstatements. |
| IPL/T20I handling | Competition scores are combined heuristically. | Missing T20I data should not be treated as zero performance. | Use sample-aware weighting, competition-specific baselines, and explicit coverage notes. |
| Validation | Only simple threshold checks are run. | This does not test ranking stability or model sensitivity. | Run multi-threshold sensitivity and recording of ranking consistency. |
