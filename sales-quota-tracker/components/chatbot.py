"""Chatbot component for querying the Sales Quota Tracker data.

This component provides a simple Streamlit chat UI and uses the Groq API to
answer questions based on the current database state (billing, quotas, clients).

The Groq API key must be set via environment variable `GROQ_API_KEY` or
Streamlit secrets `groq_api_key`.
"""

import os
import streamlit as st
import pandas as pd

from utils.llm_client import completion
from utils.billing_manager import load_billing_data
from utils.quota_manager import load_quotas
from utils.client_manager import load_clients
from utils.derived_manager import load_leaderboard, load_quota_achievement, load_salesperson_billing


def _summarize_df(df, name, max_rows=3):
    if df is None or df.empty:
        return f"{name}: (no data)\n"

    cols = ", ".join(df.columns.tolist())
    summary = [f"{name}: {len(df)} rows; columns: {cols}.\n"]

    # Include a few example rows
    sample = df.head(max_rows)
    rows = sample.to_dict(orient="records")
    for r in rows:
        summary.append(str(r) + "\n")

    return "".join(summary)


def _build_prompt(query: str) -> str:
    """Build a prompt for the Groq API that includes the dataset and user question.

    The prompt template is loaded from `prompts/chatbot_prompt.txt` if present so the
    instructions can be changed without editing code.
    """
    # Load current data from database
    billing = load_billing_data()
    quotas = load_quotas()
    clients = load_clients()

    # Narrow the data included in the prompt to keep token usage low.
    # We only include a small sample of the billing rows relevant to the query.
    month = None
    import re

    month_match = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?:uary|ch|ril|y|e|ust|tember|ober|ember)?(?:\s+\d{4})?\b", query.lower())
    if month_match:
        month = _normalize_month(month_match.group(0))

    billing_subset = billing.copy() if billing is not None else pd.DataFrame()
    if month is not None and "Month" in billing_subset.columns:
        billing_subset = billing_subset[billing_subset["Month"].astype(str).str.strip() == month]

    # Include only a sample of rows to avoid exceeding token limits.
    billing_csv = billing_subset.head(50).to_csv(index=False) if not billing_subset.empty else ""
    quotas_csv = quotas.head(50).to_csv(index=False) if quotas is not None and not quotas.empty else ""
    clients_csv = clients.head(50).to_csv(index=False) if clients is not None and not clients.empty else ""

    # Load prompt template from disk (allows customizing without editing code).
    import os

    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "chatbot_prompt.txt")
    template = None
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except Exception:
        template = None

    if not template:
        template = (
            "You are a helpful assistant that answers questions about sales billing, quotas, and client data.\n"
            "Use only the data provided below.\n"
            "If the answer cannot be found in the data, respond with \"I don't know\".\n\n"
            "=== Billing data (CSV) ===\n{billing}\n\n"
            "=== Quota targets (CSV) ===\n{quotas}\n\n"
            "=== Client master data (CSV) ===\n{clients}\n\n"
            "Question: {question}\n"
            "Answer:"
        )

    return template.format(billing=billing_csv, quotas=quotas_csv, clients=clients_csv, question=query)


def _normalize_month(month_str: str) -> str | None:
    """Normalize a month string to the Month format stored in the data (e.g. 'Jan-2026').

    Accepts values like 'Jan', 'January', 'Jan-2026', 'January 2026', etc.
    If a year is not provided, uses the current year.
    """

    if not month_str or not month_str.strip():
        return None

    from datetime import datetime

    # Remove punctuation and normalize whitespace
    cleaned = month_str.strip().replace("/", " ").replace("-", " ").replace(",", " ")
    parts = [p for p in cleaned.split() if p]
    if not parts:
        return None

    # Month name is expected first.
    month_name = parts[0][:3].title()
    try:
        month_num = datetime.strptime(month_name, "%b").month
    except ValueError:
        return None

    year = None
    if len(parts) > 1 and parts[1].isdigit():
        year = int(parts[1])
    else:
        year = datetime.now().year

    return f"{month_name}-{year}"


def _answer_from_data(query: str) -> str | None:
    """Try to answer common billing questions directly from the local dataset.

    Returns a one-line answer, or None if the query should be handled by the LLM.
    """

    import re

    billing = load_billing_data()
    if billing is None or billing.empty:
        return None

    # Normalize stored values so we can reliably match month/salesperson strings.
    billing = billing.copy()
    billing["Month"] = billing["Month"].astype(str).str.strip()
    billing["Sales Person"] = billing["Sales Person"].astype(str).str.strip()
    billing["Billing Amount"] = pd.to_numeric(billing["Billing Amount"], errors="coerce").fillna(0.0)

    q = query.strip().lower()

    # Simple greeting / non-data question handling
    if q in {"hi", "hii", "hello", "hey", "how are you"}:
        return "Hi! Ask a question about sales billing, quotas, or client data."

    # Meta question about which LLM is being used
    if "who are you" in q or "are you" in q and ("gemini" in q or "groq" in q):
        provider = "Gemini" if os.environ.get("LLM_PROVIDER", "gemini").lower() in {"gemini", "google", "google-gemini"} else "Groq"
        return f"I am a chatbot powered by {provider}."

    # Normalize month in query
    month_match = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?:uary|ch|ril|y|e|ust|tember|ober|ember)?(?:\s+\d{4})?\b", q)
    month = None
    if month_match:
        month = _normalize_month(month_match.group(0))

    # If asking about count of billings in a month
    if "how many" in q or "number" in q or "count" in q:
        if month:
            count = int((billing["Month"] == month).sum())
            return str(count)

    # If asking about total billing (including "how much billing" phrasing)
    if ("total" in q and "billing" in q) or ("how much" in q and "billing" in q):
        if month:
            df_month = billing[billing["Month"] == month]
            # Optional filter by salesperson (ignore 'both'/'all' requests)
            sp_match = re.search(r"for\s+(?:sales\s+person\s+)?([a-zA-Z]+)", q)
            if sp_match:
                sp = sp_match.group(1).lower()
                if sp not in {"both", "all", "everyone"}:
                    df_month = df_month[df_month["Sales Person"].str.lower() == sp]

            total = float(df_month["Billing Amount"].sum())
            return f"{total:.2f}"

    # If asking if any sales team exists (or what teams exist)
    if "sales team" in q or ("team" in q and "sales" in q):
        teams = billing["Sales Team"].dropna().astype(str).str.strip()
        teams = teams[teams != ""]
        if teams.empty:
            return "No sales team is present in the data."
        unique = sorted(set(teams.tolist()))
        if "present" in q or "exists" in q or "any" in q:
            return "Yes. Sales teams present: " + ", ".join(unique)
        # Otherwise, just report the teams
        return "Sales teams: " + ", ".join(unique)

    # If asking about leaderboard / top targets
    if "leaderboard" in q or "top target" in q or ("top" in q and "achievement" in q):
        leaderboard = load_leaderboard()
        if leaderboard.empty:
            return "No leaderboard data available."
        top_rows = leaderboard.head(3)
        return "; ".join(
            [f"{int(r['rank'])}. {r['entity_name']} ({r['achievement_pct']}%)" for _, r in top_rows.iterrows()]
        )

    # If asking for quota achievement details
    if "quota" in q and "achievement" in q:
        achievement = load_quota_achievement()
        if achievement.empty:
            return "No quota achievement data available."
        # Return a short summary (top 3 rows)
        top_rows = achievement.sort_values(by=["Achievement %"], ascending=False).head(3)
        return "; ".join(
            [
                f"{r['Entity Name']}: {r['Achievement %']}% (Quota {r['Quota']} vs Billing {r['Total Billing']})"
                for _, r in top_rows.iterrows()
            ]
        )

    # If asking about salesperson billing summary
    if "sales person" in q and ("billing" in q or "billing amount" in q):
        sp_bill = load_salesperson_billing()
        if sp_bill.empty:
            return "No salesperson billing data available."
        # If asking for a specific rep:
        match = re.search(r"sales person\s+([a-zA-Z]+)", q)
        if match:
            name = match.group(1).title()
            row = sp_bill[sp_bill["sales_person"].str.lower() == name.lower()]
            if not row.empty:
                return f"{name}: {float(row.iloc[0]['total_billing']):.2f}"
        # Otherwise return top 3
        top3 = sp_bill.sort_values(by=["total_billing"], ascending=False).head(3)
        return "; ".join([
            f"{r['sales_person']}: {r['total_billing']:.2f}" for _, r in top3.iterrows()
        ])

    # If asking who is the top salesperson (by total billing)
    if "top" in q and "sales" in q:
        totals = (
            billing.groupby("Sales Person")["Billing Amount"].sum().sort_values(ascending=False)
        )
        if not totals.empty:
            top_person = totals.index[0]
            top_amount = totals.iloc[0]
            return f"{top_person} ({top_amount:.2f})"

    return None


def render_chatbot():
    """Render the chatbot UI inside the dashboard."""

    st.markdown("---")
    st.subheader("📘 Data Chatbot")

    # Model selection (useful for switching between Gemini model variants)
    if "llm_model" not in st.session_state:
        st.session_state["llm_model"] = os.environ.get("GEMINI_MODEL", "models/gemini-2.5-flash")

    model_options = [
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro",
        "models/gemini-2.0-flash",
        "models/gemini-flash-latest",
        "models/gemini-pro-latest",
    ]

    st.selectbox(
        "LLM model",
        options=model_options,
        index=model_options.index(st.session_state["llm_model"]) if st.session_state["llm_model"] in model_options else 0,
        key="llm_model",
        help="Select the Gemini model to use for the chatbot.",
    )

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_question = st.text_input("Ask a question about your sales data:", key="chat_question")

    # Render chat history inside a scrollable container
    chat_html = [
        "<style>",
        "  .chat-scrollbox {",
        "    height: 420px;",
        "    overflow-y: auto;",
        "    padding-right: 8px;",
        "  }",
        "  .chat-user {",
        "    padding: 8px;",
        "    margin: 4px 0;",
        "    background: #f0f0f0;",
        "    border-radius: 8px;",
        "  }",
        "  .chat-assistant {",
        "    padding: 8px;",
        "    margin: 4px 0;",
        "    background: #eef2ff;",
        "    border-radius: 8px;",
        "  }",
        "</style>",
        "<div class='chat-scrollbox'>",
    ]

    for msg in st.session_state.get("chat_history", []):
        if msg["role"] == "user":
            chat_html.append(
                f"<div class='chat-user'><strong>You:</strong> {msg['content']}</div>"
            )
        else:
            chat_html.append(
                f"<div class='chat-assistant'><strong>Assistant:</strong> {msg['content']}</div>"
            )

    chat_html.append("</div>")
    st.markdown("\n".join(chat_html), unsafe_allow_html=True)

    # Handle new question
    if st.button("Ask", key="chat_ask") and user_question:
        st.session_state["chat_history"].append({"role": "user", "content": user_question})

        # Stream the assistant reply (use local data calculations for common queries)
        with st.chat_message("assistant"):
            response_text = ""
            try:
                data_answer = _answer_from_data(user_question)
                if data_answer is not None:
                    response_text = data_answer
                    st.write(response_text)
                else:
                    prompt = _build_prompt(user_question)
                    # Ensure selected model is used for the LLM request
                    model = st.session_state.get("llm_model")
                    if model:
                        os.environ["GEMINI_MODEL"] = model
                    for chunk in completion(prompt, model=model, stream=True):
                        response_text += chunk
                        st.write(response_text)
            except Exception as exc:
                response_text = f"Error: {exc}"
                st.write(response_text)

        st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
        st.rerun()

    st.markdown(
        "---\n" 
        "<small>To use this feature, set your Groq API key as environment variable `GROQ_API_KEY` "
        "or in `st.secrets['groq_api_key']`. The chatbot uses the qwen-72b model.</small>",
        unsafe_allow_html=True,
    )
