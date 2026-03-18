# 🚀 Sales Quota Tracker

A full-featured **Streamlit dashboard** for tracking sales performance & quota, built with:

- ✅ Azure AD Authentication (SSO)
- ✅ Upload + persist billing data (Excel/CSV)
- ✅ Quota management and tracking
- ✅ Dynamic dashboards, charts, and leaderboards
- ✅ Built-in Data Chatbot (LLM-powered)
- ✅ Light / Dark theme toggle

---

## 📌 Table of Contents

- [Features](#-features)
- [Getting Started](#-getting-started)
- [Azure AD Authentication](#-azure-ad-authentication)
- [Uploading Billing Data](#-uploading-billing-data)
- [Chatbot](#-chatbot)
- [Theme Toggle](#-theme-toggle)
- [Project Structure](#-project-structure)
- [Deployment (Azure)](#-deployment-azure)
- [Troubleshooting](#-troubleshooting)

---

## 🌟 Features

### ✅ Security & Access
- Azure AD (Entra ID) authentication for secure login
- Whitelisted users only (configured in `auth/config.py`)

### 📥 Billing Upload
- Upload Excel / CSV files
- Built-in validation + normalization
- Persists into local SQLite

### 🎯 Quota Management
- Define targets by Salesperson or Team
- Track achievement % and progress
- Update quotas via file upload or manual editing

### 📊 Interactive Dashboards
- Key metrics (Total Billing / Quota / Achievement)
- Filters: Month, Client, Salesperson
- Visualizations: charts + leaderboards

### 🧠 Smart Chatbot
- Ask questions about your billing/quota data
- Powered by LLM (Groq GPT-like model)
- Streamed responses, context-aware

### 🎨 Theme Toggle
- Light and dark themes supported
- One-click toggle in sidebar

---

## 🧰 Getting Started

### Prerequisites
- Python 3.11+
- `pip` installed

### 1) Clone the repo

```bash
git clone <repo-url>
cd sales-quota-tracker
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure Azure AD authentication (required)
Create `.streamlit/secrets.toml`:

```toml
[auth]
tenant_id = "<YOUR_TENANT_ID>"
client_id = "<YOUR_CLIENT_ID>"
client_secret = "<YOUR_CLIENT_SECRET>"
redirect_uri = "http://localhost:8501/oauth2callback"
```

> 🔒 **Never commit** `secrets.toml` to source control.

### 4) Run the app

```bash
streamlit run app.py
```

✅ Navigate to `http://localhost:8501`

---

## 🔐 Azure AD Authentication

### Required Azure Setup
1. Register an app in **Azure Active Directory**
2. Set Redirect URI to:

```text
http://localhost:8501/oauth2callback
```

3. Add API permissions (Microsoft Graph):
   - `User.Read`

4. Create a **Client Secret** (copy value immediately)

### Whitelisted Users
Authorized logins are in `auth/config.py`:

```python
ALLOWED_USERS = [
    "ayush.mittal@artesian.io",
    "priyanshu.pratap@artesian.io",
]
```

---

## 📄 Uploading Billing Data

### Required columns (case-sensitive)

- `Date` (parseable date format)
- `Type`
- `Description`
- `Sales Person`
- `Team` (mapped to `Client Name`)
- `Amount`

### Sample Row

| Date       | Type     | Description      | Sales Person | Team      | Amount |
|------------|----------|------------------|--------------|-----------|--------|
| 2026-02-01 | Service  | Monthly retainer | Priya        | Acme Corp | 50000  |

> The app automatically creates:
> - `Month` (e.g., `Feb-2026`)
> - `Billing Amount` (numeric)
> - `Client Name` (from `Team`)

---

## 🤖 Chatbot

Ask questions about your sales data via the chatbot on the Dashboard.

### Groq API Configuration

Set your API key as either:

#### Environment variable
```bash
export GROQ_API_KEY="your_key_here"
```

#### Streamlit secrets
```toml
groq_api_key = "your_key_here"
```

---

## 🎨 Theme Toggle

Toggle between light and dark mode using the sidebar button.

---

## 🏗️ Project Structure

```
├── app.py                       # Main application entry
├── auth/                       # Authentication module
│   ├── __init__.py             # Exposes auth helpers
│   ├── config.py               # Config + allowed users
│   └── manager.py              # MSAL + login handling
├── components/                 # UI components
│   ├── chatbot.py              # Chatbot view
│   ├── charts.py
│   ├── dashboard.py
│   ├── tables.py
│   └── ...
├── utils/                      # Business logic
├── data/                       # Local SQLite database
├── prompts/                    # Chatbot prompt templates
├── requirements.txt
└── README.md
```

---

## ☁️ Deployment (Azure)

### 1) Create Azure SQL / PostgreSQL
- Use managed database to store data

### 2) Containerize (Docker)
- Build a Docker image and push to ACR

### 3) Deploy to Azure App Service
- Use Docker image
- Configure environment variables and key vaults

> For a full step-by-step guide, see `DEPLOYMENT_PLAN.md`.

---

## 🛠 Troubleshooting

### Login fails
- Verify `secrets.toml` values
- Ensure Azure redirect URI matches exactly
- Confirm user is in `ALLOWED_USERS`

### Upload errors
- Validate required columns and formatting
- Ensure `data/app.db` is writable

### Chatbot doesn’t respond
- Confirm `GROQ_API_KEY` is set

---

## 📌 Notes

This project is built for small teams and internal use. For a production deployment:
- Use a shared cloud database (Azure SQL / PostgreSQL)
- Add role-based access controls
- Add monitoring & logging

---

Happy tracking! 📊
