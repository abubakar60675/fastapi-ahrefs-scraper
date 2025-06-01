from fastapi import FastAPI, HTTPException
from botasaurus.browser import browser, Driver
from botasaurus_humancursor import WebCursor
import json
import time
import base64
import asyncio
from pydantic import BaseModel
from typing import Literal

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class CheckRequest(BaseModel):
    url: str
    checkType: Literal["traffic", "dr", "both"]

# Semaphore to prevent concurrent requests
semaphore = asyncio.Semaphore(1)

def extract_api_data(parsed_data):
    """Extracts the actual data object from API response structure"""
    if isinstance(parsed_data, list) and len(parsed_data) == 2:
        return parsed_data[1]
    return parsed_data

def process_response(driver, response_info):
    """Processes API response and returns clean data"""
    try:
        response_obj = driver.collect_response(response_info["request_id"])
        content = response_obj.content
        
        if response_obj.is_base_64:
            content = base64.b64decode(content).decode('utf-8', errors='ignore')
        
        try:
            parsed_data = json.loads(content)
            return extract_api_data(parsed_data)
        except json.JSONDecodeError:
            return {"error": "Response not in JSON format"}
    except Exception as e:
        return {"error": str(e)}

def check_for_refresh(driver, initial_url, initial_title, timeout=10, interval=0.05):
    """Check if the page has refreshed/changed"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if driver.current_url != initial_url or driver.title != initial_title:
            return True
        time.sleep(interval)
    return False

@browser()
def scrape_ahrefs(driver: Driver, request: CheckRequest):
    results = {}
    domain = request.url
    check_type = request.checkType
    
    # Initialize human-like cursor
    cursor = WebCursor(driver)
    driver.enable_human_mode()
    
    # Handle traffic page if requested
    if check_type in ["traffic", "both"]:
        traffic_url = f"https://ahrefs.com/traffic-checker/?input={domain}&mode=subdomains"
        traffic_endpoint = "https://ahrefs.com/v4/stGetFreeTrafficOverview"
        traffic_response = None
        
        def traffic_handler(request_id, response, event):
            nonlocal traffic_response
            if traffic_endpoint in response.url and traffic_response is None:
                traffic_response = {
                    "url": response.url,
                    "status": response.status,
                    "request_id": request_id
                }
        
        driver.after_response_received(traffic_handler)
        
        # Use human-like navigation
        cursor.move_mouse_to_point(100, 100, True)
        driver.google_get(traffic_url, bypass_cloudflare=True)
        body = driver.get_text("body")
        
        # Wait for traffic API response with timeout
        start_time = time.time()
        while not traffic_response and (time.time() - start_time) < 30:
            time.sleep(0.5)
        
        if traffic_response:
            results["traffic"] = process_response(driver, traffic_response)
        
        driver._response_received_listeners = []
    
    # Handle backlink page if requested
    if check_type in ["dr", "both"]:
        backlink_url = f"https://ahrefs.com/backlink-checker/?input={domain}&mode=subdomains"
        backlink_endpoints = {
            "domainOverview": "https://ahrefs.com/v4/stGetFreeBacklinksOverview",
            "topBacklinksList": "https://ahrefs.com/v4/stGetFreeBacklinksList"
        }
        backlink_responses = {key: None for key in backlink_endpoints}
        
        def backlink_handler(request_id, response, event):
            url = response.url
            for key, endpoint in backlink_endpoints.items():
                if endpoint in url and backlink_responses[key] is None:
                    backlink_responses[key] = {
                        "url": url,
                        "status": response.status,
                        "request_id": request_id
                    }
        
        driver.after_response_received(backlink_handler)
        
        # Use human-like navigation
        cursor.move_mouse_to_point(100, 100, True)
        driver.google_get(backlink_url, bypass_cloudflare=True)
        
        # Wait for backlink API responses with timeout
        start_time = time.time()
        while any(backlink_responses[key] is None for key in backlink_endpoints) and (time.time() - start_time) < 30:
            time.sleep(0.5)
        
        for key, response_info in backlink_responses.items():
            if response_info:
                results[key] = process_response(driver, response_info)
    
    driver.disable_human_mode()
    return results

@app.post(
    "/check-domain",
    summary="Check Ahrefs data for a domain",
    description="""
Checks Ahrefs data for the given domain.

- `traffic`: Retrieves traffic overview only.
- `dr`: Retrieves domain rating and backlinks.
- `both`: Retrieves traffic and domain rating and backlink information.
    
**Example domains:**
- `ahrefs.com`
- `yep.com`
""",
)
async def check_domain(request: CheckRequest):
    async with semaphore:
        try:
            result = await asyncio.to_thread(scrape_ahrefs, request)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)