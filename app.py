import os
import json
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import openai

# Load API keys
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

st.set_page_config(page_title="Business Insight Generator", layout="centered")
st.title("Business Insight Generator")

def load_business_profile(uploaded_file=None):
    if uploaded_file:
        if uploaded_file.name.endswith(".json"):
            return json.load(uploaded_file)
        elif uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            return df.iloc[0].dropna().to_dict()
    else:
        df = pd.read_csv("business-profile-1.csv")
        return df.iloc[0].dropna().to_dict()

def generate_questions(profile):
    prompt = f"""
Given this business profile:

{json.dumps(profile, indent=2)}

Generate 4-6 strategic, data-driven questions a business owner might ask to improve operations, growth, or customer engagement.
Each question should be clear, concise, and actionable.
"""
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    content = res.choices[0].message["content"]
    return [q.strip(" -") for q in content.strip().split("\n") if q.strip()]

def fetch_tavily_data(query):
    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
    payload = {"query": query, "search_depth": "advanced", "include_answers": True}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def refine_insight(profile, question, tavily_data):
    top_results = tavily_data.get("results", [])[:2]
    research = "\n\n".join([r.get("content", "") for r in top_results])
    source_url = next((r.get("url") for r in top_results if r.get("url")), "https://example.com")

    prompt = f"""
Business Profile:
{json.dumps(profile)}

Insight Question:
{question}

Relevant Web Research:
{research}

Using this, provide a single, well-written recommendation that includes:
- What the business should start doing
- What the business should stop doing (if anything)
- What the business should do more of
- What the business could change to improve performance (strategy, process, messaging, etc.)

If any of these don't apply, explicitly say so in the paragraph.
Write the answer as one plain English paragraph without headings.
Also include the most relevant source URL as a separate key named 'source'.
Respond in JSON format like:
{{
  "recommendation": "...",
  "source": "..."
}}
"""
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        return json.loads(res.choices[0].message["content"].strip())
    except Exception as e:
        return {
            "recommendation": f"Error generating recommendation: {e}",
            "source": source_url
        }

uploaded_file = st.file_uploader("Upload business profile (.csv or .json)", type=["csv", "json"])
profile = load_business_profile(uploaded_file)
company = (
    profile.get("company_name")
    or profile.get("businessName")
    or profile.get("name")
    or "Unnamed Business"
)

if "questions" not in st.session_state:
    st.session_state.questions = []
if "insights" not in st.session_state:
    st.session_state.insights = {}

with st.expander("Business Profile"):
    st.json(profile)

if st.button("Generate Insight Questions"):
    st.session_state.questions = generate_questions(profile)
    st.session_state.insights = {}

if st.session_state.questions:
    st.subheader("Click a question to get a recommendation:")
    for i, q in enumerate(st.session_state.questions):
        col1, col2 = st.columns([0.05, 0.95])
        with col1:
            clicked = st.button("➡️", key=f"btn_{i}")
        with col2:
            st.markdown(f"**{q}**")

        if clicked and q not in st.session_state.insights:
            with st.spinner("Getting recommendation..."):
                tavily_data = fetch_tavily_data(q)
                insight = refine_insight(profile, q, tavily_data)
                st.session_state.insights[q] = insight

st.subheader("Ask Your Own Custom Question")
custom_q = st.text_input("Enter a business-related question here")

if st.button("Get Recommendation for My Question") and custom_q.strip():
    if custom_q not in st.session_state.insights:
        with st.spinner("Getting recommendation for your question..."):
            tavily_data = fetch_tavily_data(custom_q)
            insight = refine_insight(profile, custom_q, tavily_data)
            st.session_state.insights[custom_q] = insight

if st.session_state.insights:
    st.subheader("Recommendations")
    for question, insight in st.session_state.insights.items():
        st.markdown(f"**Q: {question}**")
        st.markdown(insight["recommendation"])
        st.markdown(f"Source: [{insight['source']}]({insight['source']})")
        st.markdown("---")

    report = {
        "company": company,
        "insights": list(st.session_state.insights.values())
    }

    st.download_button(
        label="Download Report as JSON",
        data=json.dumps(report, indent=2),
        file_name=f"{company.replace(' ', '_').lower()}_insights.json",
        mime="application/json"
    )
