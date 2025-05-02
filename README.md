Proactive Business Insight Generator – Spike1 Branch
This branch contains the proof-of-concept (POC) for a system that uses Tavily API to generate actionable business insights based on real-time web data and a provided business profile.

----------------------------------
Features
Uses Tavily to fetch up-to-date business insights from the internet

 Auto-categorizes insights into:
 Start Doing
 Stop Doing
 Do More Of
 
 Supports .json or .csv for business profiles
 Downloadable insight reports in .txt
 Optional email delivery of insights to the business owner
 Streamlit UI for live interaction

-----------------------------------
 Folder Structure:
 /Spike1
├── app.py                         # Streamlit application
├── sample_business_profile.json  # Default business profile (JSON)
├── business-profile-1.csv        # Optional business profile (CSV)
├── .env                          # Contains API keys (Tavily, email)
├── requirements.txt              # Python dependencies
└── README.md                     # This file

-------------------------------------
How to Run the App
1. Clone this branch
git clone -b Spike1 https://github.com/pranitha275/GoLogic.git
cd GoLogic
2. Set up a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
3. Install dependencies
pip install -r requirements.txt
4. Create .env with API credentials
TAVILY_API_KEY=your_tavily_api_key
# For email feature (Gmail example with App Password)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
5. Run the Streamlit app
streamlit run app.py

----------------------------------------
Example Query Inputs
"What strategies are working for DTC skincare brands in 2025?"
"How can car part ecommerce stores increase conversion rate?"
"Trends in influencer marketing for small ecommerce brands"

----------------------------------------
Email Feature
Add an email address in the UI to receive the report.
Requires a Gmail App Password if using Gmail with 2FA.

Future Enhancements
Use OpenAI for smarter insight classification
Schedule weekly auto-reports via CRON or GitHub Actions

Add multi-profile support (choose from list)
Export insights to PDF
