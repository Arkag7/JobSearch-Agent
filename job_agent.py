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
[PASTE YOUR RESUME TEXT HERE]
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
