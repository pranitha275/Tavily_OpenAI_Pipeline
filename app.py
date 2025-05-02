import os
import json
import requests
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import pandas as pd

# Load secrets
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# --- Load Business Profile ---
def load_business_profile(default_path="sample_business_profile.json", uploaded_file=None):
    try:
        if uploaded_file:
            if uploaded_file.name.endswith(".json"):
                return json.load(uploaded_file)
            elif uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
                return df.iloc[0].dropna().to_dict()  # First row as profile
        else:
            with open(default_path, "r") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Failed to load business profile: {e}")
        return {}

# --- Tavily API Call ---
def fetch_from_tavily(query):
    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
    payload = {
        "query": query,
        "search_depth": "advanced",
        "include_answers": True
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

# --- Email Report ---
def send_email_report(recipient_email, report_text):
    msg = MIMEText(report_text)
    msg["Subject"] = "Your Business Insights Report"
    msg["From"] = EMAIL_USER
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# --- Query Construction ---
def create_contextual_query(user_query, profile):
    industry = profile.get("market_position", "ecommerce business")
    goals = profile.get("goals", [])
    goal_part = ", ".join(goals[:2]) if goals else ""
    return f"{user_query}. This is for a {industry} that aims to {goal_part.lower()}."

# --- Insight Categorization ---
def categorize_insights(results):
    start, stop, more = [], [], []

    start_keywords = [
        "start", "begin", "adopt", "introduce", "implement", "test", "try", "shift to", "invest in",
        "emerging", "growing", "trending", "gain traction", "recommended", "explore", "launch", "expand into",
        "rising", "new approach", "entering", "pilot program", "top strategy", "initiating", "successful trend"
    ]
    stop_keywords = [
        "stop", "avoid", "drop", "decline", "decrease", "ineffective", "no longer working", "not working",
        "falling behind", "obsolete", "outdated", "retire", "phase out", "abandon", "cancel", "discontinue",
        "low ROI", "wasteful", "negative impact", "underperforming", "cut back on"
    ]
    more_keywords = [
        "scale", "expand", "double down", "increase", "focus more", "optimize", "enhance", "accelerate",
        "repeat", "continue", "maximize", "boost", "proven", "successful", "keep doing", "improve",
        "strong results", "continue investing", "do more of", "build on", "capitalize on", "replicate"
    ]

    for res in results["results"][:5]:
        content = res.get("content", "").lower()
        if any(kw in content for kw in start_keywords): start.append(res)
        if any(kw in content for kw in stop_keywords): stop.append(res)
        if any(kw in content for kw in more_keywords): more.append(res)

    return start[:1], stop[:1], more[:1]

def render_actionable_insight(label, insight, fallback):
    if insight:
        content = insight[0].get("content", "")[:400] + "..."
        url = insight[0].get("url", "#")
        st.markdown(f"**{label}**: {content} [See more →]({url})")
    else:
        st.markdown(f"**{label}**: {fallback}")

# --- Streamlit UI ---
st.set_page_config(page_title="Tavily Business Insight Generator", layout="centered")
st.title(" Tavily-Powered Business Insight Generator")

st.markdown("Upload a new business profile or use the default.")
uploaded_file = st.file_uploader("Upload a custom business profile (JSON) or CSV", type=["json", "csv"])

# Load business profile
profile = load_business_profile(uploaded_file=uploaded_file)
if profile:
    with st.expander(" Current Business Profile", expanded=False):
        st.json(profile)

# User input for query and email
user_query = st.text_input("Enter your business-related search query")
email_input = st.text_input("Enter your email to receive the report (optional)")

# Main logic
if st.button("Get Insights") and user_query.strip():
    with st.spinner("Fetching insights..."):
        try:
            full_query = create_contextual_query(user_query, profile)
            data = fetch_from_tavily(full_query)

            st.subheader(" Top 5 Contextualized Results:")
            report_text = f"Business Insight Report for: {profile.get('company_name', 'Unknown Business')}\n"
            report_text += f"Query: {user_query}\n\n"

            for i, result in enumerate(data["results"][:5], 1):
                title = result.get("title", "Untitled")
                url = result.get("url")
                content = result.get("content", "")[:800]
                st.markdown(f"### {i}. {title}")
                st.markdown(f"**Source:** [{url}]({url})")
                st.write(content + "...")
                st.markdown("---")
                report_text += f"{i}. {title}\nSource: {url}\n{content}...\n\n"

            # Categorized insights
            start, stop, more = categorize_insights(data)
            st.subheader(" Proactive Actionable Insights")
            render_actionable_insight("Start Doing", start, "No new actions detected.")
            render_actionable_insight("Stop Doing", stop, "No negative patterns found.")
            render_actionable_insight("Do More Of", more, "No clear patterns found.")

            # Add categorized insights to report
            def append_to_report(label, insight, fallback):
                if insight:
                    return f"{label}:\n{insight[0].get('content', '')[:500]}\nSource: {insight[0].get('url')}\n\n"
                return f"{label}:\n{fallback}\n\n"

            report_text += "\n---\nACTIONABLE INSIGHTS\n\n"
            report_text += append_to_report("Start Doing", start, "No new actions detected.")
            report_text += append_to_report("Stop Doing", stop, "No negative patterns found.")
            report_text += append_to_report("Do More Of", more, "No clear patterns found.")

            st.download_button(
                label=" Download Full Report as .txt",
                data=report_text,
                file_name="business_insights_report.txt",
                mime="text/plain"
            )

            if email_input:
                success = send_email_report(email_input, report_text)
                if success:
                    st.success(f"Report sent to {email_input}")

        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.info("Enter a query and optionally upload a profile or email.")
