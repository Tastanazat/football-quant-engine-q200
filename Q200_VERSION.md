# Q200 Engine — Version 3.1

## Project Status

Q200 V3.1 production-oriented quantitative football analysis
engine.

Current repository state:

- Core model implemented
- Data ingestion implemented
- Source validation implemented
- StatsHub OCR/review pipeline implemented
- SoccerSTATS PDF ingestion implemented
- PPI ingestion implemented
- Odds PDF ingestion implemented
- Five-source pipeline implemented
- Model LOCK implemented
- Odds-after-lock architecture enforced
- Monte Carlo implemented
- EV / No-Vig / Fair Odds implemented
- Pessimistic EV implemented
- Selection / Kelly implemented
- Portfolio bankroll risk cap implemented
- Dataset backtest implemented
- Calibration implemented
- Evaluation implemented
- Performance analysis implemented
- History / settlement implemented
- Public API implemented

## Version

Q200 V3.1

## Architecture

The Q200 architecture is divided into the following layers:

```text
INPUT SOURCES
    |
    +-- StatsHub HOME
    +-- StatsHub AWAY
    +-- SoccerSTATS
    +-- PPI
    +-- Odds
    |
    v
INGESTION
    |
    v
CANONICAL DATA
    |
    v
VALIDATION
    |
    v
TEAM STATS
    |
    v
Q200 MODEL
    |
    +-- Lambda Home
    +-- Lambda Away
    +-- Poisson
    +-- Model Probabilities
    +-- Monte Carlo
    |
    v
MODEL LOCK
    |
    v
ODDS
    |
    +-- Implied Probability
    +-- No-Vig
    +-- Fair Odds
    +-- EV
    +-- Pessimistic EV
    |
    v
SELECTION
    |
    +-- Minimum Odds Filter
    +-- Uncertainty Filter
    +-- Kelly
    +-- Portfolio Risk Cap
    |
    v
FINAL ANALYSIS
