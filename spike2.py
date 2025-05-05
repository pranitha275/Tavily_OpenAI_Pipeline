import os
import json
import requests
from dotenv import load_dotenv
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

openai.api_key = OPENAI_API_KEY

# Sample business profile
business_profile = {
    "company_name": "Max Candle Co.",
    "industry": "Consumer Goods",
    "metrics": {
        "revenue": 1200000,
        "revenue_growth_rate": 0.15,
        "gross_profit_margin": 0.48,
        "net_profit_margin": 0.12,
        "current_ratio": 1.5,
        "sales_per_employee": 125000,
        "cash_flow": 200000,
        "operating_cash_flow_ratio": 0.9,
        "burn_rate": 50000,
        "customer_acquisition_cost": 60,
        "customer_lifetime_value": 400,
        "days_sales_outstanding": 32,
        "inventory_turnover_rate": 5,
        "cost_of_goods_sold_pct": 0.52,
        "sgna_to_sales_ratio": 0.22
    }
}

# Generate benchmark search prompts
def generate_tavily_prompt(metric, industry):
    return f"What is the average {metric.replace('_', ' ')} for {industry} companies in 2024?"

# Tavily API call
def fetch_tavily_insight(query):
    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
    payload = {"query": query, "search_depth": "advanced", "include_answers": True}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

# OpenAI insight comparison
def generate_recommendation(metric, value, benchmark_summary, profile):
    prompt = f"""
Company: {profile['company_name']}
Industry: {profile['industry']}
Metric: {metric}
Company's value: {value}

Benchmark research summary:
{benchmark_summary}

Compare the company’s metric to the industry benchmark.
Write a paragraph that includes:
- What the business should start doing
- What it should stop doing (if anything)
- What it should do more of
- What it could change to improve this metric

Write in plain language. End with a source URL if available.
"""
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# Run analysis
results = []

for metric, value in business_profile["metrics"].items():
    print(f"\n📊 Processing {metric}...")
    query = generate_tavily_prompt(metric, business_profile["industry"])

    try:
        tavily_data = fetch_tavily_insight(query)
        top_result = tavily_data.get("results", [{}])[0]
        benchmark_summary = top_result.get("content", "")
        source = top_result.get("url", "https://tavily.com")

        recommendation = generate_recommendation(
            metric, value, benchmark_summary, business_profile
        )

        results.append({
            "metric": metric,
            "company_value": value,
            "benchmark_summary": benchmark_summary[:500],
            "recommendation": recommendation,
            "source": source
        })
    except Exception as e:
        print(f" Failed to process {metric}: {e}")

# Save results
with open("benchmark_insights.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nFinished! Results saved to 'benchmark_insights.json'")
