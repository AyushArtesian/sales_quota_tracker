# Sales Quota Tracker

A **Streamlit** dashboard for tracking sales quota achievement against billing data. This version includes **Azure AD authentication**, **theme toggling (light/dark)**, and a **chatbot** for querying your data.

---

## 🚀 Key Features

- **Azure AD Authentication** (OIDC)
  - Only authorized users can access the app.
  - Login is handled via Azure AD (Entra ID) and uses Streamlit’s built-in `st.login` flow.
- **Upload Billing Data (Excel/CSV)**
  - Upload billing records with required columns.
  - Data is cleaned, normalized, and saved to a local SQLite database.
- **Quota Management**
  - Create and manage quotas for Sales People or Teams.
  - Supports importing quota files for bulk updates.
- **Client Master Data**
  - Tracks client onboarding and consideration expiration.
  - Auto-detects new clients and prompts for acquisition dates.
- **Interactive Dashboard**
  - Real-time metrics, charts, and tables.
  - Filters: Month, Client, Sales Person.
- **Theme Toggle**
  - Switch between **Light** and **Dark** mode.
- **Data Chatbot**
  - Ask questions about your billing/quota data using an LLM.

---

## 🧰 Setup & Run (Local Dev)

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

> Recommended: Use a virtual environment (venv/conda).


### 2) Configure Azure AD authentication

Create `.streamlit/secrets.toml` with your Azure AD values:

```toml
[auth]
tenant_id = "<your-tenant-id>"
client_id = "<your-client-id>"
client_secret = "<your-client-secret>"
redirect_uri = "http://localhost:8501/oauth2callback"
```

> **Important**: Never commit `secrets.toml`.


### 3) Run the app

```bash
streamlit run app.py
```

Open the URL shown in your terminal (usually `http://localhost:8501`).

---

## 🧠 Azure AD Authentication

### What’s Required
- Azure AD App Registration (OIDC)
- Client ID + Client Secret
- Redirect URI: `http://localhost:8501/oauth2callback`

### Authorized Users
The app uses a whitelist configured in `auth/config.py`:

```python
ALLOWED_USERS = [
    "ayush.mittal@artesian.io",
    "priyanshu.pratap@artesian.io",
]
```

---

## 📄 Billing Upload Format

Required columns (case-sensitive):

- `Date` (parseable date)
- `Type`
- `Description`
- `Sales Person`
- `Team` (used as `Client Name` internally)
- `Amount`

### Example

| Date       | Type     | Description      | Sales Person | Team       | Amount |
|------------|----------|------------------|--------------|------------|--------|
| 2026-02-01 | Service  | Monthly retainer | Priya        | Acme Corp  | 50000  |
| 2026-02-05 | Project  | One-time setup   | Rahul        | BetaTech   | 45000  |

> The app will auto-create:
> - `Month` (e.g., `Feb-2026`)
> - `Billing Amount` (numeric conversion)
> - `Client Name` (from `Team`)

---

## 🗄️ Persistence (SQLite)

### Database Location
- `data/app.db` — local SQLite database

### Resetting
To clear all data:

```bash
rm data/app.db
rm .streamlit_cache/stage.txt
```

---

## 🧩 Project Structure

```
├── app.py                       # Main Streamlit app
├── auth/                       # Authentication module
│   ├── __init__.py             # Exports auth helpers
│   ├── config.py               # Auth config + user whitelist
│   └── manager.py              # MSAL + login logic
├── components/                 # UI component modules
│   ├── chatbot.py              # Chatbot component
│   ├── charts.py
│   ├── dashboard.py
│   ├── tables.py
│   └── ...
├── utils/                      # Business logic + persistence
├── data/                       # SQLite DB
├── prompts/                    # Chatbot prompt templates
├── requirements.txt
└── README.md
```

---

## 🤖 Chatbot (LLM)

The dashboard includes a chatbot to ask questions about your sales data.
Requires a Groq API key.

### Configuring the Groq key

- **Environment variable**:
  ```bash
  export GROQ_API_KEY="your_key_here"
  ```

- **Streamlit secrets**:
  ```toml
groq_api_key = "your_key_here"
  ```

---

## ⚙️ Theme Toggle (Light / Dark)

Use the sidebar button to switch themes.

---

## 🛠️ Troubleshooting

### Common Issues
- **Login fails**: Check `secrets.toml` values and validate redirect URI in Azure.
- **Data not saving**: Ensure `data/app.db` is writable.
- **Chatbot not responding**: Make sure `GROQ_API_KEY` is configured.

---

## 🚀 Next Steps

1. Migrate to a cloud database (Azure SQL)
2. Containerize with Docker
3. Deploy to Azure App Service

---

## 📌 Notes

- Designed for small teams & rapid iteration.
- For multi-user deployment, use a shared cloud database and proper user management.
