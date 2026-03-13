# Sales Quota Tracker

A **Streamlit** dashboard for tracking sales quota achievement against billing data, with full persistence in a local SQLite database.

## 🚀 Key Features

- **Upload Billing Data (Excel/CSV)**
  - Upload billing records with required columns (see format below).
  - Data is normalized, deduplicated, and stored in a local SQLite database.
- **Quota Management**
  - Define quotas for Sales Persons or Teams.
  - Quotas are persisted in the same SQLite database and survive app restarts.
  - Supports importing a quota export file to bulk-load quota targets.
- **Client Master Data**
  - Automatically tracks client onboarding dates and consideration expiration.
  - New clients detected on upload trigger a modal to capture acquisition dates.
- **Interactive Dashboard**
  - Metrics: Total Billing, Total Quota, Overall Achievement %.
  - Filter by Month, Client, Sales Person.
  - Charts: Achievement distribution, Monthly trend, Leaderboards.
  - Tables: Detailed achievement table with status coloring.
- **Persistence**
  - Billing data, quotas, and client master are stored in `data/app.db`.
  - Navigation stage (Quota vs Dashboard) is remembered across refresh via `.streamlit_cache/stage.txt`.

---

## 🧰 Getting Started

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

> Recommended: Use a virtual environment (venv/conda) to avoid dependency conflicts.

### 2) Run the app

```bash
streamlit run app.py
```

Open the URL shown in the terminal (typically `http://localhost:8501`).

---

## 📄 File Format (Billing Upload)

The billing upload expects the following columns (case-sensitive):

- `Date` (any parseable date format)
- `Type`
- `Description`
- `Sales Person`
- `Team` (mapped to `Client Name` internally)
- `Amount`

### Example (CSV/Excel)

| Date       | Type     | Description     | Sales Person | Team       | Amount |
|------------|----------|-----------------|--------------|------------|--------|
| 2026-02-01 | Service  | Monthly retainer | Priya        | Acme Corp  | 50000  |
| 2026-02-05 | Project  | One-time setup  | Rahul        | BetaTech   | 45000  |

> The app will automatically create these normalized columns:
> - `Month` (e.g., `Feb-2026`)
> - `Billing Amount` (numeric conversion of `Amount`)
> - `Client Name` (from `Team`)
> - `Sales Team` (currently set to a default value)

---

## 📦 Persistence & Storage

### Database (SQLite)

All key data is stored in:

- `data/app.db` — SQLite database (created automatically)

Key persisted entities:

- `BillingData` (uploaded billing rows)
- `QuotaTarget` (quota targets per person/team)
- `ClientMaster` (client onboarding & expiration info)

### Resetting Data

To reset the app data, stop Streamlit and delete:

- `data/app.db` (clears billing/quota/client data)
- `.streamlit_cache/stage.txt` (resets the selected UI stage)

---

## 🧩 Project Structure

```
├── app.py                       # Main Streamlit app
├── components/                  # UI pieces (charts, tables, dashboard)
├── utils/                       # Business logic + persistence
│   ├── db.py                    # SQLAlchemy database initialization
│   ├── models.py                # ORM models (BillingData, QuotaTarget, ClientMaster)
│   ├── billing_manager.py       # Billing upload persistence
│   ├── quota_manager.py         # Quota persistence & validation
│   ├── client_manager.py        # Client master persistence
│   ├── excel_reader.py          # Upload parsing + validation
│   └── calculations.py          # Achievement calculations
├── data/                        # SQLite database file (auto-generated)
├── requirements.txt
└── README.md
```

---

## 🛠️ Troubleshooting

- **Upload fails / missing required columns**: Ensure your file has all required columns and the column names match exactly.
- **Data not persisting**: Confirm `data/app.db` exists and is writable.
- **App always starts in quota mode**: Delete `.streamlit_cache/stage.txt` and refresh.

---

## 🙌 Notes

- This app is designed for quick iteration and small teams; it is not intended as a full multi-user production system.
- The database is local — for shared use you may need to migrate to a shared database or networked file store.
