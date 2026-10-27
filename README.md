# Slay the Spire 2 Run Analyzer

A local, interactive web dashboard that automatically parses your Slay the Spire 2 run history and visualizes your performance, card pick rates, and decision-making patterns. 

Built with Python, Pandas, Plotly, and Streamlit, this tool acts as a lightweight ETL pipeline that transforms raw, nested game JSON files into a clean, queryable analytics dashboard.

## Quick Start

You do not need to manually install dependencies or set up environments. The included run scripts will automatically create a local Python virtual environment, install the required packages, and launch the dashboard.

### 1. Clone the Repository
`git clone https://github.com/gavinsaxer/Slay-the-Spire-2-Analyzer.git`
`cd Slay-the-Spire-2-Analyzer`

### 2. Launch the Dashboard

**For Windows:**
Simply double-click the `run.bat` file in your File Explorer, or run it from your terminal:
`.\run.bat`

**For Mac / Linux:**
Grant the script execution permissions, then run it:
`chmod +x run.sh`
`./run.sh`

## How It Works

1. **Extraction:** The app navigates to your OS's local AppData or Application Support folder, bypasses your unique Steam ID, and reads the raw .run JSON files.
2. **Transformation:** A Pydantic schema adapter (core/schemas.py) validates and structures the chaotic game data, stripping out malformed or legacy data.
3. **Loading & Visualization:** The flat dictionary is loaded into a Pandas DataFrame. Streamlit renders the UI, and Plotly Express handles the interactive filtering and charting.

*Note: If you do not have Slay the Spire 2 installed on your machine, the dashboard will gracefully fall back to a provided sample dataset so you can still explore the UI.*
