# ChessDNA — Chess Player Style Analyser

A Streamlit app that predicts a player's playing style from their average game statistics, using the project's PCA + KMeans pipeline.

## Playing styles
- Tactical attacker
- Early-queen risk-taker
- Quiet / positional

## Methodology
- Player-level profiles built from Lichess Elite games (Oct 2025)
- 80/20 train-test split (`random_state=42`) before any fitting
- Median/mode imputation, ordinal and one-hot encoding
- `log1p` on skewed features, StandardScaler
- Near-constant and correlation feature filtering
- PCA retaining 90% variance, then KMeans with 3 clusters
- Logistic Regression used only to give approximate cluster probabilities for new players

Clusters are evaluated with silhouette score (low, so styles overlap). The logistic regression reproduces KMeans labels; it is not a ground-truth classifier.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Render
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
- Environment variable: `PYTHON_VERSION=3.12.8`