# PressureIQ

PressureIQ is a cricket analytics project for identifying player reliability under pressure using the supplied IPL and T20I historical data. It reconstructs match state from ball-by-ball evidence, estimates pressure by innings context, and ranks eligible batters and bowlers with transparent methodology notes.

## Important data handling

- The original raw data files in `Data Pack/` are treated as proprietary and should remain local.
- Do not commit or publish raw ball-by-ball delivery files.
- Only derived, public-safe analysis files under `outputs/` should be shared publicly.

## Quick start

1. Install dependencies:
   `python -m pip install -r requirements.txt`
2. Run the pipeline:
   `python main.py`
3. Launch the dashboard:
   `streamlit run app.py`

## Project layout

- `src/` contains the analytics modules.
- `outputs/` contains generated reports, leaderboards, charts and deployment documents.
- `tests/` contains validation tests for delivery accounting and ranking logic.
- `app.py` is the Streamlit dashboard entrypoint.

## Deployment guidance

This project is prepared for Streamlit Community Cloud. Use the repository root as the deployment root and set the app entry point to `app.py`.

Recommended deployment checklist:

1. Create a GitHub repository.
2. Commit only the project source, generated dashboard-safe outputs, and deployment configuration.
3. Keep the raw `Data Pack/` directory local and untracked or excluded from the public repo.
4. Ensure `requirements.txt` contains all Python dependencies.
5. In Streamlit Community Cloud, select the repo and set the app file to `app.py`.
6. Use Python 3.11.x in the deployment settings.
7. Push to GitHub and redeploy after changes.

## Public-safe deployment notes

- Raw proprietary data should not be published to a public repository.
- Public dashboard assets should use only approved derived statistics and scouting publications.
- The deployment guide is in `outputs/DEPLOYMENT_GUIDE.md`.

## Data source

Raw CSVs are read from `Data Pack/` and preserved without modification. The pipeline audits the offered schema, reconstructs match state, measures pressure based on match context, and ranks eligible players.
