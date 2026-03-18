# Sales Quota Tracker

A **professional Streamlit dashboard** for tracking sales billing, quota targets, and performance dashboards — built for business users, managers, and analysts.

This repository is a full solution with:

- ✅ **Secure Azure AD authentication (SSO)**
- ✅ **Billing upload + normalization (Excel / CSV)**
- ✅ **Quota planning & tracking**
- ✅ **Interactive dashboards + charts**
- ✅ **AI-powered chatbot** (analysis + insights)
- ✅ **Light / dark theme toggle**

---

## 📌 Document Outline

1. [Overview](#-overview)
2. [Architecture](#-architecture)
3. [Installation & Local Development](#-installation--local-development)
4. [Azure AD Authentication (Required)](#-azure-ad-authentication-required)
5. [Billing Data Upload](#-billing-data-upload)
6. [Quota Management](#-quota-management)
7. [Dashboard + UI Overview](#-dashboard--ui-overview)
8. [Chatbot (LLM)](#-chatbot-llm)
9. [Theme Toggle](#-theme-toggle)
10. [Project Structure](#-project-structure)
11. [Deployment (Azure)](#-deployment-azure)
12. [Troubleshooting](#-troubleshooting)
13. [Maintenance & Extension](#-maintenance--extension)

---

## 🌐 Overview

Sales Quota Tracker is designed to bring business operations and analytics together.
It supports:

- Uploading billing files and storing normalized transactions.
- Tracking quota targets across individuals and teams.
- Dashboards that show real-time performance vs quota.
- A conversational chatbot to ask questions about your data.

This tool is ideal for small-to-medium sales organizations that need a simple yet robust reporting and quota-tracking solution.

---

## 🏗️ Architecture

### Core Components

| Module | Purpose |
|--------|---------|
| `app.py` | Entry point: UI routing + orchestration |
| `auth/` | User authentication (Azure AD OIDC) |
| `components/` | UI components (charts, tables, chatbot, etc.) |
| `utils/` | Business logic (data loading, calculations, persistence) |
| `data/` | Local SQLite database storage |
| `prompts/` | Prompt templates for chatbot |

### Tech Stack

- **Streamlit**: UI & web app framework
- **SQLite (SQLAlchemy)**: Local persistence
- **Azure AD (OIDC)**: Authentication + identity
- **MSAL**: OAuth2 token handling
- **Groq/LLM**: Chatbot model

---

## 🧰 Installation & Local Development

### Prerequisites

- Python 3.11+
- `pip`

### 1) Clone the repository

```bash
git clone <repo-url>
cd sales-quota-tracker
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure Azure AD (required)

Create `.streamlit/secrets.toml` with your Azure AD values:

```toml
[auth]
tenant_id = "<YOUR_TENANT_ID>"
client_id = "<YOUR_CLIENT_ID>"
client_secret = "<YOUR_CLIENT_SECRET>"
redirect_uri = "http://localhost:8501/oauth2callback"
```

> 🔒 **Never commit** `secrets.toml` to source control.

### 4) Run locally

```bash
streamlit run app.py
```

Access: `http://localhost:8501`

---

## 🔐 Azure AD Authentication (Required)

### Setup Steps (Azure Portal)

1. Navigate to **Azure Active Directory → App registrations → New registration**
2. Set:
   - **Name:** `sales-quota-tracker`
   - **Supported account types:** `Single tenant` (your org)
   - **Redirect URI:** `http://localhost:8501/oauth2callback`
3. Click **Register**

### Configure Permissions

1. Go to **API permissions** → **Add a permission**
2. Select **Microsoft Graph** → **Delegated permissions**
3. Add **User.Read**
4. Click **Grant admin consent**

### Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Copy the **value** (not the ID!) immediately

### Configure Allowed Users

In `auth/config.py` set the approved user list:

```python
ALLOWED_USERS = [
    "ayush.mittal@artesian.io",
    "priyanshu.pratap@artesian.io",
]
```

---

## 📄 Billing Data Upload

### Required Columns (case-sensitive)

| Column | Description |
|--------|-------------|
| `Date` | Transaction date (any parseable format) |
| `Type` | Billing type (Service/Product/etc.) |
| `Description` | Description text |
| `Sales Person` | Salesperson name |
| `Team` | Client name (mapped to `Client Name`) |
| `Amount` | Numeric amount |

### Sample Row

| Date       | Type     | Description      | Sales Person | Team      | Amount |
|------------|----------|------------------|--------------|-----------|--------|
| 2026-02-01 | Service  | Monthly retainer | Priya        | Acme Corp | 50000  |

### System Normalizations

The app will automatically create:

- `Month` (e.g., `Feb-2026`)
- `Billing Amount` (numeric conversion)
- `Client Name` (from `Team`)

---

## 📌 Quota Management

### Capabilities

- Create/update quota targets per Salesperson/Team
- Compare actual billing vs quota
- Track achievement percentage

### Where it lives

- UI: Dashboard / Quota Editor screens
- Data stored in: `data/app.db`

---

## 📊 Dashboard & UI Overview

### Main Dashboard

- Key metrics: Total billing, total quota, achievement %
- Filtering by month/client/salesperson
- Charts: trend analysis, leaderboards

### Dark + Light Theme

- Toggle button in sidebar
- Theme is persisted in session state (not in DB)

---

## 🤖 Chatbot (LLM)

### How it works

- Uses the conversation model to answer questions
- Combines billing/quota data + prompt template
- UI lives on the Dashboard page

### Required configuration

#### Environment variable
```bash
export GROQ_API_KEY="your_key_here"
```

#### Streamlit secrets
```toml
groq_api_key = "your_key_here"
```

---

## 🧩 Project Structure

```
├── app.py                       # Streamlit entrypoint
├── auth/                       # Authentication module
│   ├── __init__.py             # Public auth exports
│   ├── config.py               # Allowed users / auth settings
│   └── manager.py              # MSAL + login flow
├── components/                 # UI components
│   ├── chatbot.py              # Chatbot UI
│   ├── charts.py               # Visualization components
│   ├── dashboard.py            # Main dashboard layout
│   ├── tables.py               # Data tables
│   └── ...
├── utils/                      # Business logic & persistence
│   ├── db.py                   # SQLAlchemy Init
│   ├── models.py               # ORM models
│   ├── billing_manager.py      # Billing ingest + cleanup
│   ├── quota_manager.py        # Quota persistence
│   └── ...
├── data/                       # SQLite database
├── prompts/                    # Chatbot prompt templates
├── requirements.txt            # Python dependencies
└── README.md                   # This doc
```

---

## ☁️ Deployment (Azure)

### Recommended Architecture

1. **Azure SQL / PostgreSQL** for shared data storage
2. **Azure Container Registry (ACR)** for Docker images
3. **Azure App Service** for hosting the Streamlit app
4. **Azure Key Vault** for secrets

### Quick Deployment Steps (High-Level)

1. Create Azure SQL / PostgreSQL instance
2. Build Docker image:
   ```bash
docker build -t sales-quota-tracker:latest .
```
3. Push to ACR:
   ```bash
az acr login --name <registry>
docker tag sales-quota-tracker:latest <registry>.azurecr.io/sales-quota-tracker:latest
docker push <registry>.azurecr.io/sales-quota-tracker:latest
```
4. Create App Service (Docker) and point to ACR image
5. Set environment variables / Key Vault references

> See `DEPLOYMENT_PLAN.md` for full step-by-step deployment instructions.

---

## 🛠 Troubleshooting

### Login fails
- Confirm `secrets.toml` matches Azure AD app settings
- Make sure `redirect_uri` in Azure matches exactly
- Confirm user is listed in `auth/config.py`

### Data upload errors
- Validate missing or incorrect column names
- Ensure `data/app.db` is writable

### Chatbot not responding
- Verify `GROQ_API_KEY` is configured
- Confirm the model selection is valid

---

## 🔧 Extending the App

### Adding new metrics
1. Update `utils/calculations.py` with new logic
2. Add UI tiles in `components/dashboard.py`

### Adding new chatbot behavior
1. Update `prompts/chatbot_prompt.txt`
2. Update `components/chatbot.py` parsing logic

---

## 📌 Notes

This project is built to be: 
- modular (clean folder separation)
- extensible (easy to add pages/components)
- secure (Azure AD auth + whitelist)

For production use, consider:
- shared database (Azure SQL)
- multi-tenant access control
- logging / monitoring

---

Happy tracking! 📈
