# Sales Quota Tracker

A **Streamlit** application for tracking sales quota achievement against billing data.

## Features

- **Excel Upload** – Upload billing records (`.xlsx`) with columns: Client Name, Month, Billing Amount, Freelancer, Sales Person.
- **Data Aggregation** – Automatically aggregates billing by Client × Month.
- **Manual Quota Entry** – Set quotas via an editable table or individual number inputs; persisted to CSV.
- **Achievement Calculation** – Computes `Achievement % = (Billing / Quota) × 100` and assigns status (Achieved / Almost Achieved / Not Achieved).
- **Dashboard Metrics** – Total Billing, Total Quota, Overall Achievement %.
- **Sidebar Filters** – Filter by Month, Client, Sales Person.
- **Interactive Charts** (Plotly) – Billing vs Quota, Sales Person Performance, Achievement Distribution, Monthly Trend.
- **Detailed Tables** – Colour-coded achievement table with all metrics.
- **Leaderboard** – Top clients and sales persons ranked by billing.

## Project Structure

```
sales-quota-tracker/
├── app.py                  # Main Streamlit application
├── components/
│   ├── dashboard.py        # KPI metrics & sidebar filters
│   ├── charts.py           # Plotly visualisations
│   ├── quota_input.py      # Quota entry UI
│   └── tables.py           # Achievement table & leaderboard
├── utils/
│   ├── excel_reader.py     # Excel file parsing & validation
│   ├── aggregator.py       # Data aggregation helpers
│   ├── quota_manager.py    # Quota persistence (session state + CSV)
│   └── calculations.py     # Achievement computation
├── data/
│   └── quota_data.csv      # Persisted quotas (auto-generated)
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Then open the URL shown in the terminal (typically `http://localhost:8501`).

## Excel File Format

| Client Name | Month    | Billing Amount | Freelancer | Sales Person |
|-------------|----------|----------------|------------|--------------|
| Acme Corp   | Jan-2026 | 50000          | Alice      | Rahul        |
| BetaTech    | Jan-2026 | 45000          | Bob        | Priya        |

## Tech Stack

- **Streamlit** – UI framework
- **Pandas** – Data manipulation
- **Plotly** – Interactive charts
- **openpyxl** – Excel file reading
