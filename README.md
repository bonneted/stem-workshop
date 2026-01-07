# Quarter Car Simulation Web App

A Python web application that simulates a quarter car suspension model driving over a bump. This is a conversion of a MATLAB GUI application to a web-based interface using Dash and Plotly.

## Features

- **Interactive sliders** to adjust:
  - Suspension stiffness (Ks)
  - Damping coefficient (Cs)
  - Tire stiffness (Kt)
  - Vehicle speed

- **Real-time animation** showing the car model, springs, and damper

- **Displacement plot** showing sprung and unsprung mass motion over time

## Local Development

### Prerequisites

- [uv](https://docs.astral.sh/uv/) for package and project management

### Installation

```bash
uv sync
```

### Running Locally

```bash
uv run app.py
```

Then open http://localhost:8050 in your browser.

## Deployment to Railway

### Option 1: Deploy via GitHub

1. Push this `python/` folder to a GitHub repository

2. Go to [Railway](https://railway.app/) and create a new project

3. Select "Deploy from GitHub repo" and connect your repository

4. Railway will automatically detect the `Procfile` and deploy

5. Add environment variable (optional):
   - `PORT`: Railway sets this automatically

### Option 2: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project (from the python/ directory)
railway init

# Deploy
railway up
```

## Project Structure

```
matlab/             # MATLAB files

app.py              # Main Dash web application
simulation.py       # Quarter car physics (state-space model)
plotting.py         # Plotly visualization functions
requirements.txt    # Python dependencies
Procfile            # Railway/Heroku deployment config
runtime.txt         # Python version specification
README.md           # This file
```

## Physics Model

The simulation uses a quarter car model with:
- **Sprung mass (M)**: 1500 kg (vehicle body)
- **Unsprung mass (m)**: 150 kg (wheel/tire assembly)
- **Suspension spring (Ks)**: Adjustable stiffness
- **Damper (Cs)**: Adjustable damping
- **Tire spring (Kt)**: Adjustable tire stiffness

The state-space model is solved using `scipy.signal.lsim` for accurate dynamic response.
