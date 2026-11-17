# Deployment Guide

## 1. Create or use a GitHub repository

1. Create a new private or public GitHub repo for the PressureIQ project.
2. Push the repository content from this workspace.
3. Keep the local raw data directory outside the public repo if it is proprietary.

## 2. Files safe to commit

- `app.py`
- `main.py`
- `config.yaml`
- `requirements.txt`
- `README.md`
- `src/`
- `tests/`
- `outputs/` generated public-safe summaries and charts
- `.streamlit/config.toml`

## 3. Files that must remain private

- `Data Pack/`
- `__MACOSX/`
- Any raw ball-by-ball delivery files
- Any sensitive proprietary match records

## 4. Streamlit Community Cloud setup

1. Open: https://share.streamlit.io/
2. Sign in with GitHub.
3. Authorize the repository.
4. Select the repo.
5. Set the app path to `app.py`.
6. Set the Python version to 3.11.
7. Choose the default branch.
8. Deploy.

## 5. Verify deployment

After deployment, confirm:

- The app loads without errors.
- The dashboard shows tables and charts.
- Output files are read correctly.
- No raw proprietary data is exposed.

## 6. Update after a push

- Commit changes to GitHub.
- Streamlit Community Cloud rebuilds automatically on push.
- Re-verify the app after the rebuild.

## 7. Data security note

Do not publish raw CSVs or full delivery-level data. Only share derived public-safe analytics and scouting results.
