import os
import time
import asyncio
from fastapi import FastAPI, BackgroundTasks

# --- Initialize FastAPI Web Server ---
app = FastAPI()

def run_job_search():
    """
    Your primary job searching, Gemini evaluating, 
    and Telegram notification logic goes inside here.
    """
    # ... Insert your existing job search code inside this function ...
    
    # IMPORTANT: Inside your job evaluation loop, add a short delay
    # between Gemini API calls to prevent the 503 UNAVAILABLE rate limit:
    # time.sleep(2)


@app.get("/")
def home():
    # Satisfies Render's health check on $PORT
    return {"status": "Job Search Agent is live and healthy"}


@app.get("/run")
def trigger_agent(background_tasks: BackgroundTasks):
    # Allows you to trigger job search on demand via URL
    background_tasks.add_task(run_job_search)
    return {"status": "Job search task started in background"}


@app.on_event("startup")
async def startup_event():
    # Automatically triggers job search as soon as Render starts the web server
    asyncio.create_task(asyncio.to_thread(run_job_search))
