import os
import json
import time
import requests
import pandas as pd
from google import genai
from jobspy import scrape_jobs

# Fetch keys securely from GitHub Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- PASTE YOUR ACTUAL RESUME TEXT BELOW ---
RESUME_TEXT = """
[ARKADEV CHAKRABARTI
ENTERPRISE ACCOUNT MANAGER | KEY & STRATEGIC ACCOUNTS | COMMERCIAL OPERATIONS
CUSTOMER SUCCESS | SERVICE DELIVERY | REVENUE & O2C
Kolkata, India | Enterprise Account Management | Commercial Operations
PROFESSIONAL SUMMARY
Enterprise Account Management and Commercial Operations professional with 13+ years of B2B experience across manufacturing, industrial services and supply-chain environments. Manage strategic enterprise relationships across 25+ manufacturing locations, serving as SPOC for commercial execution, customer success, service governance and end-to-end A2C/O2C operations. Manage industrial surplus-material mandates covering approximately 68,500 MT and ₹20+ Cr annual transaction value. Achieved 120% of revenue target in FY23 and 114% in FY24 while maintaining ~95% enterprise client retention. Experienced in buyer development, revenue realization, working-capital support, commercial analytics, SLA governance and process improvement, including approximately 25% reduction in O2C cycle time.
CORE COMPETENCIES
• Enterprise & Strategic Account Management: Enterprise Account Management, Strategic Account Management, Key Account Management, Customer Success, Client Retention, Account Growth
• Commercial Operations: Commercial Governance, Asset Monetization, Industrial e-Auctions, Auction-to-Cash (A2C), Order-to-Cash (O2C), Revenue Realization, Working Capital Support
• Service & Performance: Executive Stakeholder Management, Service Delivery, SLA Governance, Escalation Management, KPI Management, Executive MIS, Commercial Analytics, Business Process Improvement
• Systems & Tools: SAP SD/MM, SAP FICO Integration, Procure-to-Pay (P2P), RACE Industrial e-Auction Platform, Advanced Excel, Microsoft 365
PROFESSIONAL EXPERIENCE
Enterprise Account Manager – Commercial Operations & Strategic Accounts (SPOC – East & North India) 
| Mjunction Services Limited | 12/2015 – Present | Kolkata
• Manage strategic enterprise relationships across 25+ manufacturing locations, serving as SPOC for commercial operations, customer success, service governance and end-to-end A2C/O2C for industrial surplus-material mandates covering approximately 68,500 MT and ₹20+ Cr annual transaction value.
• Achieved 120% of revenue target in FY23 and 114% in FY24 through strategic account management, customer engagement, service excellence and commercial execution.
• Own the end-to-end industrial e-auction lifecycle covering auction planning, catalogue creation, bidding, payment realization, delivery order issuance, dispatch planning and post-sales support.
• Develop auction catalogues by validating material specifications, commercial terms, statutory requirements, photographs, lot details and reserve-price inputs to support transparent auctions and effective price discovery.
• Coordinate with category managers and plant stakeholders to formulate auction strategies using historical transactions, buyer behaviour, market intelligence, commodity trends and demand assessment.
• Strengthen industrial buyer participation through market mapping, bidder development, relationship management and continuous engagement, contributing to auction competitiveness and revenue realization.
• Govern EMD validation, payment reconciliation, refund management, delivery-order approval, contractual compliance, dispatch coordination, lifting schedules and commercial issue resolution.
• Drive working-capital support by accelerating payment realization, monitoring outstanding transactions and ageing, and improving conversion of surplus inventory into cash.
• Lead cross-functional commercial and operational escalations with Commercial, Plant Operations, Category Management, Finance, Logistics, IT and Customer teams; maintain approximately 95% enterprise client retention.
• Designed KPI-driven MIS dashboards covering revenue realization, payment realization, auction status, order ageing, SLA adherence, dispatch progress and escalation trends, contributing to approximately 25% reduction in O2C cycle time.
• Conduct QBRs, operational reviews and executive stakeholder discussions to improve account governance, service delivery and issue resolution.
• Ensure SAP SD/MM transaction accuracy with SAP FICO integration across commercial documentation, billing, delivery and financial controls.

Senior Executive – Sales Operations & Commercial Support | Greenply Industries Limited | 07/2015 – 12/2015 | Kolkata
• Managed end-to-end O2C activities from customer RFQs and order processing through invoicing, dispatch and payment coordination.
• Served as SPOC for pan-India customers, coordinating with Sales, Procurement, Warehouse, Logistics, Finance and Customer Service.
• Supported procurement of imported materials, commercial documentation, customs-clearance coordination and supplier interactions.
• Executed SAP SD/MM activities including sales orders, goods receipt, PGI, inventory movements and billing.
• Resolved delivery and service issues while supporting SLA and contractual commitments to improve customer experience.
Executive – Strategic Sourcing & Commercial Operations | ABP Pvt. Ltd. | 01/2014 – 07/2015 | Kolkata
• Supported strategic sourcing, warehouse operations, inventory planning and logistics to enable production continuity.
• Managed SAP SD/MM procurement and inventory transactions, stock reconciliation and commercial documentation.
• Prepared KPI/MIS reporting covering Inventory Accuracy, OTIF, TAT, Stock Availability and Warehouse Productivity.
• Coordinated 3PL operations and transport activities with Production, Procurement, Finance, Quality and Logistics teams.
• Supported inventory optimisation and process improvements to strengthen supply-chain efficiency.
SELECTED ACHIEVEMENTS
• 120% revenue target achievement – FY23.
• 114% revenue target achievement – FY24.
• Approximately 68,500 MT industrial surplus-material mandate managed with ₹20+ Cr annual transaction value.
• Approximately 95% enterprise client retention across strategic accounts.
• Approximately 25% O2C cycle-time reduction through KPI-driven dashboards and process controls.
• Supported multimodal evacuation of secondary/scrap materials through prepaid rake movement during COVID-related operational disruption, supporting uninterrupted plant operations and receiving multiple client appreciations.
EDUCATION
• MBA – Marketing & Operations | IIEST Shibpur | CGPA: 7.00
• B.Tech – Electronics & Communication Engineering | Techno India College of Technology | CGPA: 8.13
CERTIFICATIONS & PROFESSIONAL DEVELOPMENT
• Google Project Management Professional Certificate – Foundation
• Managing Project Stakeholders
• HubSpot Inbound Sales Operation	
]
"""

SEARCH_ROLE = "Enterprise Account Management"
SEARCH_LOCATION = "Kolkata"
HOURS_LOOKBACK = 24
RESULTS_CEILING = 15  # Capped to 15 jobs per run to prevent API quota overload
MINIMUM_SCORE = 6

client = genai.Client(api_key=GEMINI_API_KEY)

def send_telegram_alert(title, company, score, reasoning, url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return
    
    message = (
        f"🎯 <b>New Job Match Found ({score}/10)!</b>\n\n"
        f"💼 <b>Role:</b> {title}\n"
        f"🏢 <b>Company:</b> {company}\n\n"
        f"📝 <b>Reasoning:</b> {reasoning}\n\n"
        f"🔗 <a href='{url}'>Click Here to Apply</a>"
    )
    
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    try:
        response = requests.post(telegram_url, json=payload)
        if response.status_code == 200:
            print("📱 Telegram notification sent!")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Error sending alert: {e}")

# 1. Scrape Jobs
print(f"🔍 Searching for '{SEARCH_ROLE}' jobs in {SEARCH_LOCATION}...")
try:
    jobs = scrape_jobs(
        site_name=["linkedin", "indeed"],
        search_term=SEARCH_ROLE,
        location=SEARCH_LOCATION,
        country_indeed="india",
        linkedin_fetch_description=True,
        results_wanted=RESULTS_CEILING,
        hours_old=HOURS_LOOKBACK,
    )
    print(f"✅ Found {len(jobs)} total job(s) posted today!")
except Exception as e:
    print(f"Error scraping: {e}")
    jobs = pd.DataFrame()

# 2. Gemini Resume Evaluator
def evaluate_job_match(description):
    prompt = f"""
    You are an expert HR recruiter. Evaluate how well this candidate's resume fits the job description.

    Resume:
    {RESUME_TEXT}

    Job Description:
    {description}

    Return ONLY a valid JSON object with no markdown formatting backticks:
    {{
      "score": <number between 1 and 10>,
      "reasoning": "<2 sentence summary of why it fits or does not fit>"
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as err:
        return {"score": 0, "reasoning": f"API Error: {err}"}

# 3. Process & Alert
if not jobs.empty:
    for idx, job in jobs.iterrows():
        title = job.get('title', 'N/A')
        company = job.get('company', 'N/A')
        description = job.get('description', '')
        job_url = job.get('job_url', '#')

        if not description or pd.isna(description) or len(str(description).strip()) < 50:
            print(f"⏩ Skipping: '{title}' at {company} (No description)")
            continue

        print(f"Evaluating ({idx+1}/{len(jobs)}): {title} at {company}")
        evaluation = evaluate_job_match(description)
        score = evaluation.get("score", 0)
        reason = evaluation.get("reasoning", "")

        print(f"  ➜ Fit Score: {score}/10")
        print(f"  ➜ Reason: {reason}\n")

        if score >= MINIMUM_SCORE:
            send_telegram_alert(title, company, score, reason, job_url)

        # 15 second delay between requests to stay under 5 req/min free rate limit
        time.sleep(15)
